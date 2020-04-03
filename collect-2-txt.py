#! /usr/bin/env python3

# (c) Kazansky137 - Fri Apr  3 21:26:57 UTC 2020

import sys
import os
import signal
import atexit

from common import log, adsb_ca
from time import time

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient
from discover import Discover


class MyClient(TcpClient):
    def handler_hup(self, _signum, _frame):
        self.signal_hup = 1

    def handler_int(self, _signum, _frame):
        self.signal_int = 1

    def __init__(self, _host, _port, _datatype):
        TcpClient.__init__(self, _host, _port, _datatype)

        self.discover = Discover()

        # Signals handling
        self.signal_hup = 0
        self.signal_int = 0
        signal.signal(signal.SIGHUP, self.handler_hup)
        signal.signal(signal.SIGINT, self.handler_int)

    def handle_messages(self, _messages):
        for msg, ts in _messages:
            # log(self.discover.message(msg))
            if self.discover.message(msg)['ret'] < 0:
                continue

            # Exit on SIGINT
            if self.signal_int == 1:
                self.signal_int = 0
                self.discover.logstat()
                sys.exit(1)

            # Printout of statistics
            if self.signal_hup == 1:
                self.signal_hup = 0
                self.discover.logstat()

            if(len(msg) == 26 or len(msg) == 40):
                # Some version of dump1090 have the 12 first characters used w/
                # some date (timestamp ?). E.g. sdbr245 feeding flightradar24.
                # Strip 12 first characters.
                msg = msg[12:]

            dfmt = pms.df(msg)
            icao = pms.icao(msg)

            # Aircraft identification
            if dfmt == 17 or dfmt == 18:    # Downlink format 17 or 18

                if pms.crc(msg) != 0:
                    continue

                tc = pms.typecode(msg)
                if tc == 4:          # Type code
                    cs = pms.adsb.callsign(msg)
                    ca = self.discover.ca_txt(adsb_ca(msg))
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
