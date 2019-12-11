#! /usr/bin/env python3

# (c) Kazansky137 - Wed Dec 11 11:42:02 CET 2019

import alert
from common import log
import sys
import os
import signal
from time import gmtime, strftime


class Flight():

    def __init__(self, _ic, _ts, _sq=None, _cs=None):
        self.data = {'ic': _ic,         # Icao hex code
                     'fs': float(_ts),  # First seen
                     'ls': float(_ts),  # Last seen
                     'sq': _sq,         # Squawk
                     'cs': _cs,         # Call sign
                     'nm': 1}           # Number of messages

    def print(self, _file=sys.stdout):
        print("{:s} {:s} {:s} {:s} {:>8s} {:5d} {:7.1f}".format
              (strftime("%d %H:%M:%S", gmtime(self.data['fs'])),
               strftime("%d %H:%M:%S", gmtime(self.data['ls'])),
               self.data['ic'], str(self.data['sq']), str(self.data['cs']),
               self.data['nm'], self.data['ls'] - self.data['fs']
               ), file=_file)


class FlightList():
    def handler_hup(self, _signum, _frame):
        self.signal_hup = 1

    def __init__(self):
        self.list = []
        self.alerts = alert.AlertList()

        self.signal_hup = 0
        signal.signal(signal.SIGHUP, self.handler_hup)

    def add(self, _fl):
        self.list.insert(0, _fl)

    def print(self, _file=sys.stdout):
        cnt = 0
        for flx in reversed(self.list):
            flx.print(_file)
            cnt = cnt + flx.data['nm']
        return cnt

    def addupd_flight(self, _ts, _ic, _sq=None, _cs=None):
        if self.signal_hup == 1:
            self.signal_hup = 0
            self.alerts.reload()

        for flx in self.list:
            if flx.data['ic'] == _ic:
                # log("Existing flight for icao",
                #     _ic, flx.data['sq'], flx.data['cs'], flx.data['nm'])

                if _sq is not None:
                    if flx.data['sq'] is not None:
                        if flx.data['sq'] != _sq:
                            new_fl = Flight(_ic, _ts, _sq, _cs)
                            # log("New flight from squawk", _sq, new_fl.data)
                            self.add(new_fl)
                            alx = self.alerts.check(_ic, _ts, _sq, _cs)
                            if alx is not None:
                                alx.log(_ts)
                            return
                        else:
                            alx = self.alerts.check(_ic, _ts, _sq, _cs)
                            if alx is not None:
                                alx.log(_ts)
                    else:
                        flx.data['sq'] = _sq
                        alx = self.alerts.check(_ic, _ts, _sq, _cs)
                        if alx is not None:
                            alx.log(_ts)

                if _cs is not None:
                    if flx.data['cs'] is not None:
                        if flx.data['cs'] != _cs:
                            new_fl = Flight(_ic, _ts, _sq, _cs)
                            # log("New flight from callsn", _cs, new_fl.data)
                            self.add(new_fl)
                            alx = self.alerts.check(_ic, _ts, _sq, _cs)
                            if alx is not None:
                                alx.log(_ts)
                            return
                        else:
                            alx = self.alerts.check(_ic, _ts, _sq, _cs)
                            if alx is not None:
                                alx.log(_ts)
                    else:
                        # log("Updated call sign", _cs)
                        flx.data['cs'] = _cs
                        alx = self.alerts.check(_ic, _ts, _sq, _cs)
                        if alx is not None:
                            alx.log(_ts)

                flx.data['ls'] = float(_ts)
                flx.data['nm'] = flx.data['nm'] + 1

                return

        try:
            new_fl = Flight(_ic, _ts, _sq, _cs)
            self.add(new_fl)
            # log("New flight", new_fl.data)
            alx = self.alerts.check(_ic, _ts, _sq, _cs)
            if alx is not None:
                alx.log(_ts)

        except:
            pass

if __name__ == "__main__":

    log("Running: Pid {:5d}".format(os.getpid()))

    fl = FlightList()

    cnt = 0
    for line in sys.stdin:
        cnt = cnt + 1
        # log("Read", line, end='')
        if cnt % 250000 == 0:
            log("Running   : Read {:>12,d} messages".format(cnt))
        words = line.split()
        if len(words) == 4:
            fl.addupd_flight(words[0], words[2], _sq=words[3])
        elif len(words) == 5:
            fl.addupd_flight(words[0], words[2], _cs=words[4])
        # log("\n")

    nmsgs = fl.print()

    log("Terminated: Read {:>12,d} messages".format(nmsgs))

    sys.exit(0)
