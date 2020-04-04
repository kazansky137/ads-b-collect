#! /usr/bin/env python3

# (c) Kazansky137 - Sat Apr  4 17:12:00 UTC 2020

import sys
import os
from time import time
from common import log, adsb_ca
import pyModeS as pms


ca_msg = ["None",   # 0 - No ADSB-Emitter
          "Light",  # 1 - Light < 15500 lbs
          "Small",  # 2 - Small   15500 to  75000 lbs
          "Large",  # 3 - 75000 to 300000 lbs
          "HVort",  # 4 - High Vortex Large (aircraft such as B-757)
          "Heavy",  # 5 - Heavy > 300000 lbs
          "HPerf",  # 6 - High Performance > 5 g acceleration and > 400 kts
          "Rotor"   # 7 - Rotorcraft
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

    def __init__(self):
        self.msgs_curr_total = 0
        self.msgs_curr_len28 = 0
        self.msgs_curr_short = 0

        self.msgs_last_total = 0
        self.msgs_last_len28 = 0
        self.msgs_last_short = 0

        self.df = [0] * 32          # Downlink Format : 5 bits  1 ..  5
        self.ca = [0] * 8           # capability      : 3 bits  6 ..  8
        self.tc = [0] * 32          # Type Code       : 5 bits 33 .. 37

        self.parity_check_ok = 0
        self.parity_check_ko = 0

        self.check_legacy_ok = 0
        self.check_legacy_ko = 0

        # Time counters
        self.t_curr = time()
        self.t_last = time()

    def ca_txt(self, index):
        return ca_msg[index]

    def message(self, msg):
        ret_dict = {}

        self.msgs_curr_total = self.msgs_curr_total + 1

        if len(msg) == 26 or len(msg) == 40:
            # Some version of dump1090 have the 12 first characters used w/
            # some date (timestamp ?). E.g. sdbr245 feeding flightradar24.
            # Strip 12 first characters.
            msg = msg[12:]

        if len(msg) < 28:        # Message length 112 bits
            self.msgs_curr_short = self.msgs_curr_short + 1
            ret_dict['ret'] = -1
            return ret_dict

        self.msgs_curr_len28 = self.msgs_curr_len28 + 1

        if pms.crc(msg) == 0:
            self.parity_check_ok = self.parity_check_ok + 1
        else:
            self.parity_check_ko = self.parity_check_ko + 1

        if pms.crc_legacy(msg) == 0:
            self.check_legacy_ok = self.check_legacy_ok + 1
        else:
            self.check_legacy_ko = self.check_legacy_ko + 1

        dfmt = pms.df(msg)
        ret_dict['dfmt'] = dfmt
        self.df[dfmt] = self.df[dfmt] + 1

        ret_dict['ic'] = pms.icao(msg)

        if dfmt in [17, 18]:    # Downlink format 17 or 18
            tc = pms.typecode(msg)
            ret_dict['tc'] = tc
            self.tc[tc] = self.tc[tc] + 1
            if tc == 4:
                ret_dict['cs'] = pms.adsb.callsign(msg)
                ca = adsb_ca(msg)
                ret_dict['ca'] = ca
                self.ca[ca] = self.ca[ca] + 1
        elif dfmt in [5, 21]:
                ret_dict['sq'] = pms.idcode(msg)

        ret_dict['ret'] = 0
        return ret_dict

    def logstat(self):
        # Time
        self.t_last = self.t_curr
        self.t_curr = time()
        self.t_diff = self.t_curr - self.t_last

        # Messages
        delta_total = self.msgs_curr_total - self.msgs_last_total
        delta_len28 = self.msgs_curr_len28 - self.msgs_last_len28
        delta_short = self.msgs_curr_short - self.msgs_last_short

        delta_total = int(delta_total / self.t_diff)
        delta_len28 = int(delta_len28 / self.t_diff)
        delta_short = int(delta_short / self.t_diff)

        self.msgs_last_total = self.msgs_curr_total
        self.msgs_last_len28 = self.msgs_curr_len28
        self.msgs_last_short = self.msgs_curr_short

        log("Running   : Raw Read  {:>12,d} messages ({:5d} /s)"
            .format(self.msgs_last_total, int(delta_total)))
        log("Running   : Raw Read  {:>12,d} msglen28 ({:5d} /s)"
            .format(self.msgs_last_len28, int(delta_len28)))
        log("Running   : Raw Read  {:>12,d} msgshort ({:5d} /s)"
            .format(self.msgs_last_short, int(delta_short)))

        log("Running   : Raw Read  {:>12,d} check ok"
            .format(self.parity_check_ok))
        log("Running   : Raw Read  {:>12,d} check ko"
            .format(self.parity_check_ko))

        log("Running   : Raw Read  {:>12,d} check legacy ok"
            .format(self.check_legacy_ok))
        log("Running   : Raw Read  {:>12,d} check legacy ko"
            .format(self.check_legacy_ko))

        for i in range(len(self.df)):
            v = self.df[i]
            if v > 0:
                log("Running   : Raw Read  {:>12,d} dfmt[{:2d}]"
                    .format(v, i))

        s = 0
        for i in range(len(self.ca)):
            v = self.ca[i]
            if v > 0:
                s = s + v
                log("Running   : Raw Read  {:>12,d} ca[{:2d}] {:s}"
                    .format(v, i, ca_msg[i]))
        log("Running   : Raw Read  {:>12,d} ca cnt".format(s))

        s = 0
        for i in range(len(self.tc)):
            v = self.tc[i]
            if v > 0:
                s = s + v
                log("Running   : Raw Read  {:>12,d} tc17[{:2d}] {:s}"
                    .format(v, i, tc_msg[i-1]))
        log("Running   : Raw Read  {:>12,d} tc17 cnt".format(s))


if __name__ == "__main__":

    log("Running: Pid {:5d}".format(os.getpid()))

    disc = Discover()
    cnt = 0

    for line in sys.stdin:
        cnt = cnt + 1
        # log("Read", line, end='')
        words = line.split()
        disc.message(words[1])

    disc.logstat()

    sys.exit(0)
