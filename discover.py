#! /usr/bin/env python3

# (c) Kazansky137 - Sun Mar 22 18:27:31 UTC 2020

import sys
import os
from time import time
from common import log


class Discover:

    def __init__(self):
        self.msgs_curr_total = 0
        self.msgs_curr_len28 = 0
        self.msgs_curr_short = 0

        self.msgs_last_total = 0
        self.msgs_last_len28 = 0
        self.msgs_last_short = 0

        # Time counters
        self.t_curr = time()
        self.t_last = time()

    def message(self, msg):
        self.msgs_curr_total = self.msgs_curr_total + 1

        if(len(msg) == 26 or len(msg) == 40):
            # Some version of dump1090 have the 12 first characters used w/
            # some date (timestamp ?). E.g. sdbr245 feeding flightradar24.
            # Strip 12 first characters.
            msg = msg[12:]

        if len(msg) < 28:        # Message length 112 bits
            self.msgs_curr_short = self.msgs_curr_short + 1
            return

        self.msgs_curr_len28 = self.msgs_curr_len28 + 1

        return

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


if __name__ == "__main__":
    log("Running: Pid {:5d}".format(os.getpid()))

    sys.exit(0)
