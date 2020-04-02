#! /usr/bin/env python3

# (c) Kazansky137 - Thu Apr  2 20:30:41 UTC 2020

import sys
import os
from time import time
from common import log, catxt
import pyModeS as pms


tc_txt = ["Aircraft identification",                   # 01
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

        self.downlink_format = [0] * 32     # 5 bits  1 ..  5
        self.ads_b_type_code = [0] * 32     # 5 bits 33 .. 37

        self.parity_check_ok = 0
        self.parity_check_ko = 0

        self.check_legacy_ok = 0
        self.check_legacy_ko = 0

        # Time counters
        self.t_curr = time()
        self.t_last = time()

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
        self.downlink_format[dfmt] = self.downlink_format[dfmt] + 1

        ret_dict['ic'] = pms.icao(msg)

        if dfmt in [17, 18]:    # Downlink format 17 or 18
            tc = pms.typecode(msg)
            self.ads_b_type_code[tc] = self.ads_b_type_code[tc] + 1
            if tc == 4:
                ret_dict['cs'] = pms.adsb.callsign(msg)
                ret_dict['ca'] = catxt(msg)
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

        for i in range(len(self.downlink_format)):
            v = self.downlink_format[i]
            if v > 0:
                log("Running   : Raw Read  {:>12,d} dfmt[{:2d}]"
                    .format(v, i))

        s = 0
        for i in range(len(self.ads_b_type_code)):
            v = self.ads_b_type_code[i]
            if v > 0:
                s = s + v
                log("Running   : Raw Read  {:>12,d} tc17[{:2d}] {:s}"
                    .format(v, i, tc_txt[i-1]))
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
