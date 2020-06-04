#! /usr/bin/env python3

# (c) Kazansky137 - Thu Jun  4 20:25:47 UTC 2020

import sys
import os
from time import time
from common import log, adsb_ca, load_config
from pyModeS import common, adsb
from tsmessage import TsMessage
import traceback
import signal
import re
from common import print_config
import cProfile

params = {}
load_config(params, "config/config.txt")
_debug = 1 if params['arg_debug'] else 0

ca_msg = ["None",   # 0 - No ADSB-Emitter
          "Light",  # 1 - Light < 15500 lbs
          "Small",  # 2 - Small   15500 to  75000 lbs
          "Large",  # 3 - 75000 to 300000 lbs
          "HVort",  # 4 - High Vortex Large (aircraft such as B-757)
          "Heavy",  # 5 - Heavy > 300000 lbs
          "HPerf",  # 6 - High Performance > 5 g acceleration and > 400 kts
          "Rotor"   # 7 - Rotorcraft
          ]

df_msg = ["ADS-B 56 bits Short air to air ACAS BDS 0.E",    # 00
          "",                                               # 01
          "",                                               # 02
          "",                                               # 03
          "ADS-B 56 bits Surveillance altitude",            # 04
          "ADS-B 56 bits Surveillance identity",            # 05
          "",                                               # 06
          "",                                               # 07
          "",                                               # 08
          "",                                               # 09
          "",                                               # 10
          "ADS-B 56 bits Mode-S only all call reply",       # 11
          "",                                               # 12
          "",                                               # 13
          "",                                               # 14
          "",                                               # 15
          "",                                               # 16
          "ADS-B ES (112 bits) BDS 0.[5..9]",               # 17
          "",                                               # 18
          "",                                               # 19
          "Mode-S EHS altitude reply BDS [4,5,6].0",        # 20
          "Mode-S EHS identity reply BDS [4,5,6].0",        # 21
          "",                                               # 22
          "",                                               # 23
          "",                                               # 24
          "",                                               # 25
          "",                                               # 26
          "",                                               # 27
          "",                                               # 28
          "",                                               # 29
          "",                                               # 30
          ""                                                # 31
          ]

tc_msg = ["Aircraft identification",                   # 01
          "Aircraft identification",                   # 02
          "Aircraft identification",                   # 03
          "Aircraft identification",                   # 04
          "Surface position",                          # 05
          "Surface position",                          # 06
          "Surface position",                          # 07
          "Surface position",                          # 08
          "Airborne position (w/ Baro Altitude)",      # 09
          "Airborne position (w/ Baro Altitude)",      # 10
          "Airborne position (w/ Baro Altitude)",      # 11
          "Airborne position (w/ Baro Altitude)",      # 12
          "Airborne position (w/ Baro Altitude)",      # 13
          "Airborne position (w/ Baro Altitude)",      # 14
          "Airborne position (w/ Baro Altitude)",      # 15
          "Airborne position (w/ Baro Altitude)",      # 16
          "Airborne position (w/ Baro Altitude)",      # 17
          "Airborne position (w/ Baro Altitude)",      # 18
          "Airborne velocities",                       # 19
          "Airborne position (w/ GNSS Height)",        # 20
          "Airborne position (w/ GNSS Height)",        # 21
          "Airborne position (w/ GNSS Height)",        # 22
          "Reserved",                                  # 23
          "Reserved",                                  # 24
          "Reserved",                                  # 25
          "Reserved",                                  # 26
          "Reserved",                                  # 27
          "Aircraft status",                           # 28
          "Target state and status information",       # 29
          "",                                          # 30
          "Aircraft operation status"                  # 31
          ]


class Discover:
    def handler_hup(self, _signum, _frame):
        self.signal_hup = 1

    def __init__(self):
        self.msgs_discovered = 0

        self.msgs_curr_rread = 0
        self.msgs_curr_total = 0
        self.msgs_curr_len28 = 0
        self.msgs_curr_short = 0

        self.msgs_last_rread = 0
        self.msgs_last_total = 0
        self.msgs_last_len28 = 0
        self.msgs_last_short = 0

        self.df = [0] * 32          # Downlink Format : 5 bits  1 ..  5
        self.ca = [0] *  8          # Capability      : 3 bits  6 ..  8
        self.tc = [0] * 32          # Type Code       : 5 bits 33 .. 37

        self.parity_check_ok = 0
        self.parity_check_ko = 0

        self.exc_unavailable = 0
        self.exc_missing     = 0
        self.exc_velocity    = 0
        self.exc_heading     = 0
        self.exc_rocd        = 0
        self.exc_crc_ko      = 0
        self.exc_icao_null   = 0
        self.exc_other       = 0

        # Time counters
        self.t_curr = time()
        self.t_last = time()

        # Signals handling
        self.signal_hup = 0
        signal.signal(signal.SIGHUP, self.handler_hup)

    def check_msg(self, msg):
        df = common.df(msg)
        msglen = len(msg)
        if df == 17 and msglen == 28:
            if common.crc(msg) == 0:
                return True
        elif df in [20, 21] and msglen == 28:
            return True
        elif df in [4, 5, 11] and msglen == 14:
            return True
        else:
            return False

    def ca_txt(self, index):
        return ca_msg[index]

    def message(self, msg):
        # Printout of statistics
        if self.signal_hup == 1:
            self.logstats()
            self.signal_hup = 0

        ret_dict = {}
        ret_dict['ret'] = 0
        ret_dict['type'] = ""

        self.msgs_curr_total = self.msgs_curr_total + 1

        if len(msg) == 26 or len(msg) == 40:
            # Some version of dump1090 have the 12 first characters used w/
            # some date (timestamp ?). E.g. sdbr245 feeding flightradar24.
            # Strip 12 first characters.
            msg = msg[12:]

        if len(msg) < 28:        # Message length 112 bits
            self.msgs_curr_short = self.msgs_curr_short + 1
        else:
            self.msgs_curr_len28 = self.msgs_curr_len28 + 1

        ret_dict['crc'] = self.check_msg(msg)
        if ret_dict['crc']:
            self.parity_check_ok = self.parity_check_ok + 1
        else:
            self.parity_check_ko = self.parity_check_ko + 1

        # Do not manage messages with bad CRC
        if ret_dict['crc'] is not True:
            raise ValueError("Exc_Crc_KO")

        dfmt = common.df(msg)
        ret_dict['dfmt'] = dfmt
        self.df[dfmt] = self.df[dfmt] + 1

        ret_dict['ic'] = common.icao(msg)
        if ret_dict['ic'] == '000000':
            raise ValueError("Exc_Icao_Null")

        if dfmt in [17, 18]:    # Downlink format 17 or 18
            tc = common.typecode(msg)
            ret_dict['tc'] = tc
            self.tc[tc] = self.tc[tc] + 1

            lat_ref = float(params['lat'])
            long_ref = float(params['long'])

            if tc == 4:         # Aircraft identification
                self.msgs_discovered = self.msgs_discovered + 1
                ret_dict['type'] = "CS"
                ret_dict['cs'] = adsb.callsign(msg)
                ca = adsb_ca(msg)
                ret_dict['ca'] = ca_msg[ca]
                self.ca[ca] = self.ca[ca] + 1
            elif 9 <= tc <= 18:
                self.msgs_discovered = self.msgs_discovered + 1
                ret_dict['type'] = "LB"
                ret_dict['altb'] = adsb.altitude(msg)
                (lat, long) = adsb.position_with_ref(msg, lat_ref, long_ref)
                ret_dict['lat'] = lat
                ret_dict['long'] = long
            elif tc == 19:
                self.msgs_discovered = self.msgs_discovered + 1
                ret_dict['type'] = "VH"
                _dict = adsb.velocity(msg)
                if _dict is None:
                    raise ValueError("Exc_Velocity_None")
                (ret_dict['speed'], ret_dict['head'],
                 ret_dict['rocd'], var) = _dict
                if ret_dict['head'] is None:
                    raise ValueError("AdsbHeading")
                if ret_dict['rocd'] is None:
                    raise ValueError("Exc_Rocd_None")
            elif 20 <= tc <= 22:
                self.msgs_discovered = self.msgs_discovered + 1
                ret_dict['type'] = "LG"
                ret_dict['altg'] = adsb.altitude(msg)
                (lat, long) = adsb.position_with_ref(msg, lat_ref, long_ref)
                ret_dict['lat'] = lat
                ret_dict['long'] = long
        elif dfmt in [5, 21]:
                self.msgs_discovered = self.msgs_discovered + 1
                ret_dict['type'] = "SQ"
                ret_dict['sq'] = common.idcode(msg)

        if dfmt in [0, 4, 16, 20]:
            self.msgs_discovered = self.msgs_discovered + 1
            ret_dict['type'] = "AL"
            _alt = common.altcode(msg)
            alt = _alt if _alt is not None else 0
            ret_dict['alt'] = alt

        return ret_dict

    def logstats(self, _prefix="Running"):
        # Time
        self.t_last = self.t_curr
        self.t_curr = time()
        self.t_diff = self.t_curr - self.t_last

        # Messages
        delta_rread = self.msgs_curr_rread - self.msgs_last_rread
        delta_total = self.msgs_curr_total - self.msgs_last_total
        delta_len28 = self.msgs_curr_len28 - self.msgs_last_len28
        delta_short = self.msgs_curr_short - self.msgs_last_short

        delta_rread = int(delta_rread / self.t_diff)
        delta_total = int(delta_total / self.t_diff)
        delta_len28 = int(delta_len28 / self.t_diff)
        delta_short = int(delta_short / self.t_diff)

        self.msgs_last_rread = self.msgs_curr_rread
        self.msgs_last_total = self.msgs_curr_total
        self.msgs_last_len28 = self.msgs_curr_len28
        self.msgs_last_short = self.msgs_curr_short

        log("{:10s} : Raw Read  {:>12,d} raw read ({:5d} /s)"
            .format(_prefix, self.msgs_last_rread, int(delta_rread)))
        log("{:10s} : Raw Read  {:>12,d} messages ({:5d} /s)"
            .format(_prefix, self.msgs_last_total, int(delta_total)))
        log("{:10s} : Raw Read  {:>12,d} msglen28 ({:5d} /s)"
            .format(_prefix, self.msgs_last_len28, int(delta_len28)))
        log("{:10s} : Raw Read  {:>12,d} msgshort ({:5d} /s)"
            .format(_prefix, self.msgs_last_short, int(delta_short)))

        log("{:10s} : Raw Read  {:>12,d} check ok"
            .format(_prefix, self.parity_check_ok))
        log("{:10s} : Raw Read  {:>12,d} check ko"
            .format(_prefix, self.parity_check_ko))

        log("{:10s} : Raw Read  {:>12,d} discovered"
            .format(_prefix, self.msgs_discovered))

        log("{:10s} : Raw Read  {:>12,d} exceptions resource unavailable"
            .format(_prefix, self.exc_unavailable))
        log("{:10s} : Raw Read  {:>12,d} exceptions missing message"
            .format(_prefix, self.exc_missing))
        log("{:10s} : Raw Read  {:>12,d} exceptions missing velocity"
            .format(_prefix, self.exc_velocity))
        log("{:10s} : Raw Read  {:>12,d} exceptions missing heading"
            .format(_prefix, self.exc_heading))
        log("{:10s} : Raw Read  {:>12,d} exceptions missing rocd"
            .format(_prefix, self.exc_rocd))
        log("{:10s} : Raw Read  {:>12,d} exceptions crc ko"
            .format(_prefix, self.exc_crc_ko))
        log("{:10s} : Raw Read  {:>12,d} exceptions icao null"
            .format(_prefix, self.exc_icao_null))
        log("{:10s} : Raw Read  {:>12,d} exceptions unknown"
            .format(_prefix, self.exc_other))

        s = 0
        for i in range(len(self.df)):
            v = self.df[i]
            if v > 0:
                s = s + v
                log("{:10s} : Raw Read  {:>12,d} dfmt[{:2d}] {:s}"
                    .format(_prefix, v, i, df_msg[i]))
        log("{:10s} : Raw Read  {:>12,d} df cnt".format(_prefix, s))

        s = 0
        for i in range(len(self.tc)):
            v = self.tc[i]
            if v > 0:
                s = s + v
                log("{:10s} : Raw Read  {:>12,d} tc17[{:2d}] {:s}"
                    .format(_prefix, v, i, tc_msg[i-1]))
        log("{:10s} : Raw Read  {:>12,d} tc17/18 cnt".format(_prefix, s))

        s = 0
        for i in range(len(self.ca)):
            v = self.ca[i]
            if v > 0:
                s = s + v
                log("{:10s} : Raw Read  {:>12,d} ca[{:2d}] {:s}"
                    .format(_prefix, v, i, ca_msg[i]))
        log("{:10s} : Raw Read  {:>12,d} ca cnt".format(_prefix, s))


if __name__ == "__main__":
    log("Starting   : Pid {:5d}".format(os.getpid()))

    if params['arg_profile']:
        log("Starting   : Profiling On")
        pr = cProfile.Profile()
        pr.enable()

    if params['arg_output'] == "raw":
        print(params['vers'], params['name'])

    disc = Discover()

    cnt = 0
    first_line = True

    for line in sys.stdin:
        if first_line:
            first_line = False
            regex = re.compile('(%MBR24-[1-3].0) ([A-Z\-]+)$')
            result = regex.match(line)
            if result is None:
                raise ValueError("Invalid magic characters")
            log("Starting   : Magic line", result.group(1), result.group(2))
            params['in_vers'] = result.group(1)
            params['in_name'] = result.group(2)
            if params['in_vers'] == "%MBR24-3.0":
                word_one = 0
                word_two = 1
            elif params['in_vers'] == "%MBR24-2.0":
                word_one = 1
                word_two = 2
            elif params['in_vers'] == "%MBR24-1.0":
                word_one = 0
                word_two = 1
            else:
                raise ValueError("Invalid input version")
            continue

        if _debug:
            log("debug read:", line, end='')

        if line[0] == '#':
            continue

        cnt = cnt + 1
        disc.msgs_curr_rread = disc.msgs_curr_rread + 1

        words = line.split()
        try:
            ts_msg = TsMessage(words[word_one], words[word_two])
            ret_dict = disc.message(words[word_two])
            if ret_dict['ret'] == 0:
                if params['arg_icao'] is None or \
                   params['arg_icao'] == ret_dict['ic']:
                    ts_msg.disc(ret_dict)
                    if params['arg_output'] == "legacy":
                        ts_msg.print_legacy()
                    elif params['arg_output'] == "raw":
                        ts_msg.print_raw()
                    elif params['arg_output'] == "json":
                        ts_msg.print()

        except IndexError as e:
            if len(words) == 1:
                disc.exc_missing = disc.exc_missing + 1
                if _debug:
                    log("debug exception: line {:10d}: Missing message"
                        .format(cnt+1))
            else:
                log("Exception: line {:10d}: {:s} {:s}".
                    format(cnt, str(type(e)), str(e)))
        except ValueError as e:
            if words[0] in ["Unexpected", "Error:"]:
                disc.exc_unavailable = disc.exc_unavailable + 1
                if _debug:
                    log("debug exception: line {:10d}: Resource unavailable"
                        .format(cnt+1))
            elif str(e) == "Exc_Velocity_None":
                disc.exc_velocity = disc.exc_velocity + 1
                log("Exception  : Line {:17d}: Velocity none".format(cnt+1))
            elif str(e) == "AdsbHeading":
                disc.exc_heading = disc.exc_heading + 1
                log("Exception  : Line {:10d}: Adsb heading none".format(cnt+1))
            elif str(e) == "Exc_Rocd_None":
                disc.exc_rocd = disc.exc_rocd + 1
                log("Exception  : Line {:17d}: Rocd None".format(cnt+1))
            elif str(e) == "Exc_Crc_KO":
                disc.exc_crc_ko = disc.exc_crc_ko + 1
                if _debug:
                    log("Exception  : Line {:17d} Crc KO Debug".format(cnt+1))
            elif str(e) == "Exc_Icao_Null":
                disc.exc_icao_null = disc.exc_icao_null + 1
                if _debug:
                    log("Exception  : Line {:17d} Icao Null".format(cnt+1))
            else:
                disc.exc_other = disc.exc_other + 1
                log("Exception  : Line {:17d} {:s} {:s}".
                    format(cnt+1, str(type(e)), str(e)))
        except Exception as e:
            disc.exc_other = disc.exc_other + 1
            log("Exception: line {:10d}: {:s} {:s}".
                format(cnt+1, str(type(e)), str(e)))
            log(traceback.format_exc())

    disc.logstats("Terminated")

    if params['arg_profile']:
        pr.disable()
        pr.dump_stats(params['arg_profile'])

    sys.exit(0)
