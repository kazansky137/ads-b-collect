#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 20:49:27 UTC 2020

import sys
import os
import signal
import atexit
import json

from common import log, load_config
from time import time

from pyModeS.extra.tcpclient import TcpClient
from tsmessage import TsMessage

params = {}
load_config(params, "config/config.txt")


class MyClient(TcpClient):
    def handler_hup(self, _signum, _frame):
        self.signal_hup = 1

    def handler_int(self, _signum, _frame):
        self.signal_int = 1

    def __init__(self, _host, _port, _datatype):
        TcpClient.__init__(self, _host, _port, _datatype)

        # Messages counters
        self.msgs_curr_total = 0
        self.msgs_last_total = 0

        # Time counters
        self.t_curr = time()
        self.t_last = time()

        # Signals handling
        self.signal_hup = 0
        self.signal_int = 0
        signal.signal(signal.SIGHUP, self.handler_hup)
        signal.signal(signal.SIGINT, self.handler_int)

    def logstats(self):
        # Time
        self.t_last = self.t_curr
        self.t_curr = time()
        self.t_diff = self.t_curr - self.t_last

        # Messages
        delta_total = self.msgs_curr_total - self.msgs_last_total
        delta_total = int(delta_total / self.t_diff)
        self.msgs_last_total = self.msgs_curr_total

        log("Running   : Raw Read  {:>12,d} messages ({:5d} /s)"
            .format(self.msgs_last_total, int(delta_total)))

    def handle_messages(self, _ts_messages):
        for _msg, _ts in _ts_messages:
            # Exit on SIGINT
            if self.signal_int == 1:
                self.signal_int = 0
                self.logstats()
                sys.exit(1)

            # Printout of statistics
            if self.signal_hup == 1:
                self.logstats()
                self.signal_hup = 0

            ts_msg = TsMessage(_ts, _msg)
            ts_msg.print_raw()

            self.msgs_curr_total = self.msgs_curr_total + 1


def handler_atexit():
    log("Terminated")


if __name__ == "__main__":
    atexit.register(handler_atexit)

    log("Running: Pid {:5d}".format(os.getpid()))

    host = params['addr']
    port = params['port']
    type = params['type']

    print(params['vers'], params['name'])

    client = MyClient(_host=host, _port=port, _datatype=type)
    client.run()

    sys.exit(0)
