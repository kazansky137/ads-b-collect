#! /usr/bin/env python3

# (c) Kazansky137 - Mon May 11 20:45:32 UTC 2020

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
        self.params = {}
        load_config(self.params, "config/config.txt")

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
        self.ca = [0] * 8           # capability      : 3 bits  6 ..  8
        self.tc = [0] * 32          # Type Code       : 5 bits 33 .. 37

        self.parity_check_ok = 0
        self.parity_check_ko = 0

        self.exc_unavailable = 0
        self.exc_missing = 0
        self.exc_velocity = 0
        self.exc_crc_ko = 0
        self.exc_other = 0

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
            raise ValueError("CrcKO")

        dfmt = common.df(msg)
        ret_dict['dfmt'] = dfmt
        self.df[dfmt] = self.df[dfmt] + 1

        ret_dict['ic'] = common.icao(msg)

        if dfmt in [17, 18]:    # Downlink format 17 or 18
            tc = common.typecode(msg)
            ret_dict['tc'] = tc
            self.tc[tc] = self.tc[tc] + 1

            lat_ref = float(self.params["lat"])
            long_ref = float(self.params["long"])

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
                    raise ValueError("AdsbVelocity")
                (ret_dict['speed'], ret_dict['head'],
                 ret_dict['rocd'], var) = _dict
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

    def logstats(self):
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

        log("Running   : Raw Read  {:>12,d} raw read ({:5d} /s)"
            .format(self.msgs_last_rread, int(delta_rread)))
        log("Running   : Raw Read  {:>12,d} messages ({:5d} /s)"
            .format(self.msgs_last_total, int(delta_total)))
        log("Running   : Raw Read  {:>12,d} msglen28 ({:5d} /s)"
            .format(self.msgs_last_len28, int(delta_len28)))
        log("Running   : Raw Read  {:>12,d} msgshort ({:5d} /s)"
            .format(self.msgs_last_short, int(delta_short)))

        log("Running   : Raw Read  {:>12,d} discovered"
            .format(self.msgs_discovered))

        log("Running   : Raw Read  {:>12,d} check ok"
            .format(self.parity_check_ok))
        log("Running   : Raw Read  {:>12,d} check ko"
            .format(self.parity_check_ko))

        log("Running   : Raw Read  {:>12,d} exceptions resource unavailable"
            .format(self.exc_unavailable))
        log("Running   : Raw Read  {:>12,d} exceptions missing message"
            .format(self.exc_missing))
        log("Running   : Raw Read  {:>12,d} exceptions missing velocity      *"
            .format(self.exc_velocity))
        log("Running   : Raw Read  {:>12,d} exceptions crc ko                *"
            .format(self.exc_crc_ko))
        log("Running   : Raw Read  {:>12,d} exceptions other                 ?"
            .format(self.exc_other))

        s = 0
        for i in range(len(self.df)):
            v = self.df[i]
            if v > 0:
                s = s + v
                log("Running   : Raw Read  {:>12,d} dfmt[{:2d}] {:s}"
                    .format(v, i, df_msg[i]))
        log("Running   : Raw Read  {:>12,d} df cnt".format(s))

        s = 0
        for i in range(len(self.tc)):
            v = self.tc[i]
            if v > 0:
                s = s + v
                log("Running   : Raw Read  {:>12,d} tc17[{:2d}] {:s}"
                    .format(v, i, tc_msg[i-1]))
        log("Running   : Raw Read  {:>12,d} tc17/18 cnt".format(s))

        s = 0
        for i in range(len(self.ca)):
            v = self.ca[i]
            if v > 0:
                s = s + v
                log("Running   : Raw Read  {:>12,d} ca[{:2d}] {:s}"
                    .format(v, i, ca_msg[i]))
        log("Running   : Raw Read  {:>12,d} ca cnt".format(s))


if __name__ == "__main__":

    log("Running: Pid {:5d}".format(os.getpid()))

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
            log(result.group(1), result.group(2))
            disc.params['in_vers'] = result.group(1)
            disc.params['in_name'] = result.group(2)
            if disc.params['in_vers'] == "%MBR24-3.0":
                word_one = 0
                word_two = 1
            elif disc.params['in_vers'] == "%MBR24-2.0":
                word_one = 1
                word_two = 2
            elif disc.params['in_vers'] == "%MBR24-1.0":
                word_one = 0
                word_two = 1
            else:
                raise ValueError("Invalid input version")
            continue
        cnt = cnt + 1
        if disc.params["debug"]:
            log("Read", line, end='')
        disc.msgs_curr_rread = disc.msgs_curr_rread + 1
        words = line.split()
        try:
            ts_msg = TsMessage(words[word_one], words[word_two])
            ret_dict = disc.message(words[word_two])
            if ret_dict['ret'] == 0:
                ts_msg.disc(ret_dict)
                # ts_msg.print()
                ts_msg.print_legacy()

        except IndexError as e:
            if len(words) == 1:
                disc.exc_missing = disc.exc_missing + 1
                log("Exception: line {:10d}: Missing message".format(cnt+1))
            else:
                log("Exception: line {:10d}: {:s} {:s}".
                    format(cnt, str(type(e)), str(e)))
        except ValueError as e:
            if words[0] in ["Unexpected", "Error:"]:
                disc.exc_unavailable = disc.exc_unavailable + 1
                log("Exception: line {:10d}: Resource unavailable"
                    .format(cnt+1))
            elif str(e) == "AdsbVelocity":
                disc.exc_velocity = disc.exc_velocity + 1
                log("Exception: line {:10d}: Adsb velocity none".format(cnt+1))
            elif str(e) == "CrcKO":
                disc.exc_crc_ko = disc.exc_crc_ko + 1
                if disc.params["debug"]:
                    log("Exception: line {:10d}: CRC check failure"
                        .format(cnt+1))
            else:
                log("Exception: line {:10d}: {:s} {:s}".
                    format(cnt+1, str(type(e)), str(e)))
        except Exception as e:
            disc.exc_other = disc.exc_other + 1
            log("Exception: line {:10d}: {:s} {:s}".
                format(cnt+1, str(type(e)), str(e)))
            log(traceback.format_exc())

    disc.logstats()

    sys.exit(0)
