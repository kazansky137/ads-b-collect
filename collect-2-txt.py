#! /usr/bin/env python3

# (c) Kazansky137 - Mon Mar 16 21:41:12 UTC 2020

import sys
import os
import signal
import atexit

from common import log
from time import time

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient


class MyClient(TcpClient):
    def handler_hup(self, _signum, _frame):
        self.signal_hup = 1

    def handler_int(self, _signum, _frame):
        self.signal_int = 1

    def __init__(self, _host, _port, _datatype):
        TcpClient.__init__(self, _host, _port, _datatype)

        # Message counters
        self.msgs_curr_total = 0
        self.msgs_curr_len28 = 0
        self.msgs_curr_short = 0

        self.msgs_last_total = 0
        self.msgs_last_len28 = 0
        self.msgs_last_short = 0

        # Time counters
        self.t_curr = time()
        self.t_last = time()

        # Signals handling
        self.signal_hup = 0
        self.signal_int = 0
        signal.signal(signal.SIGHUP, self.handler_hup)
        signal.signal(signal.SIGINT, self.handler_int)

    def ca(self, _msg):
        """
        0 : No ADS-B Emitter Category Information
        1 : Light < 15500 lbs.
        2 : Small   15500 to  75000 lbs.
        3 : Large   75000 to 300000 lbs.
        4 : High Vortex Large (aircraft such as B-757)
        5 : Heavy > 300000 lbs.
        6 : High Performance > 5 g acceleration and > 400 kts
        7 : Rotorcraft
        """
        dfbin = pms.hex2bin(_msg[:2])
        return pms.bin2int(dfbin[5:8])

    def catxt(self, _msg):
        ca = ['None ', 'Light', 'Small', 'Large',
              'HVort', 'Heavy', 'HPerf', 'Rotor']
        return ca[self.ca(_msg)]

    def handle_messages(self, _messages):
        for msg, ts in _messages:
            # Exit on SIGINT
            if self.signal_int == 1:
                sys.exit(1)

            # Printout of statistics
            if self.signal_hup == 1:
                self.signal_hup = 0

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

                log("Running   : Read {:>12,d} messages ({:5d} /s)"
                    .format(self.msgs_last_total, int(delta_total)))
                log("Running   : Read {:>12,d} msglen28 ({:5d} /s)"
                    .format(self.msgs_last_len28, int(delta_len28)))
                log("Running   : Read {:>12,d} msgshort ({:5d} /s)"
                    .format(self.msgs_last_short, int(delta_short)))

            self.msgs_curr_total = self.msgs_curr_total + 1

            if( len(msg) == 26 or len(msg) == 40 ):
            # Some version of dump1090 have the 12 first characters used with
            # some date (timestamp ?). E.g. sdbr245 feeding flightradar24.
            # Strip 12 first characters.
                msg = msg[12:]

            if len(msg) < 28:        # Message length 112 bits
                self.msgs_curr_short = self.msgs_curr_short + 1
                continue

            self.msgs_curr_len28 = self.msgs_curr_len28 + 1

            dfmt = pms.df(msg)
            icao = pms.icao(msg)

            # Aircraft identification
            if dfmt == 17 or dfmt == 18:    # Downlink format 17 or 18
                tc = pms.typecode(msg)
                if tc == 4:          # Type code
                    cs = pms.adsb.callsign(msg)
                    ca = self.catxt(msg)
                    print("{:15.9f} {:s} {:s} {:s} {:s}".format
                          (ts, msg, icao, ca, cs), flush=True)
            elif dfmt in [5, 21]:
                    sq = pms.idcode(msg)
                    print("{:15.9f} {:s} {:s} {:s}".format
                          (ts, msg, icao, sq), flush=True)


def handler_atexit():
    log("Terminated")


if __name__ == "__main__":
    atexit.register(handler_atexit)

    log("Running: Pid {:5d}".format(os.getpid()))

    host = sys.argv[1]
    port = int(sys.argv[2])
    type = sys.argv[3]

    client = MyClient(_host=host, _port=port, _datatype=type)
    client.run()

    sys.exit(0)
