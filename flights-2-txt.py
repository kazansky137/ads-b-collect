#! /usr/bin/env python3

# (c) Kazansky137 - Sat Apr 11 21:14:29 UTC 2020

import alert
from common import log
import sys
import os
import signal
from time import gmtime, strftime, time
import importlib
icaocodes = importlib.import_module("icao-codes")


class Flight():

    def __init__(self, _ic, _ts, _sq=None, _cs=None, _alt='0'):
        self.data = {'ic': _ic,         # Icao hex code
                     'fs': float(_ts),  # First seen
                     'ls': float(_ts),  # Last seen
                     'sq': _sq,         # Squawk
                     'cs': _cs,         # Call sign
                     'nm': 1}           # Number of messages

        self.pos = {'alt_fs': int(_alt),   # Altitude first seen
                    'alt_ls': int(_alt),   # "        last seen
                    'alt_min': int(_alt),  # "        minimum
                    'alt_max': int(_alt)}  # "        maximum

    def print(self, _file=sys.stdout):
        if _file == sys.stderr and (self.data['nm'] < 16 or
           (time() - self.data['ls']) > 60):
            return

        print("{:s} {:s} {:s} {:s} {:>8s} {:5d} {:7.1f} {:5d} {:5d} {:5d} {:5d}"
              .format(strftime("%d %H:%M:%S", gmtime(self.data['fs'])),
                      strftime("%d %H:%M:%S", gmtime(self.data['ls'])),
                      self.data['ic'], str(self.data['sq']),
                      str(self.data['cs']), self.data['nm'],
                      self.data['ls'] - self.data['fs'],
                      self.pos['alt_fs'], self.pos['alt_ls'],
                      self.pos['alt_min'], self.pos['alt_max']), file=_file)


class FlightList():
    codes = icaocodes.IcaoCodes()

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

    def addupd_flight(self, _ts, _ic, _sq=None, _cs=None, _alt='0'):
        if self.signal_hup == 1:
            self.signal_hup = 0
            self.alerts.reload()
            self.print(_file=sys.stderr)
            sys.stderr.flush()

        for flx in self.list:
            if flx.data['ic'] == _ic:
                # log("Existing flight for icao",
                #     _ic, flx.data['sq'], flx.data['cs'], flx.pos['alt_ls'], flx.data['nm'])

                if _sq is not None:
                    if flx.data['sq'] is not None:
                        if flx.data['sq'] != _sq:
                            new_fl = Flight(_ic, _ts, _sq, _cs, _alt)
                            # log("New flight from squawk", _sq, new_fl.data, new_fl.pos)
                            self.add(new_fl)
                            self.alerts.check(_ic, _ts, _sq, _cs)
                            return
                        else:
                            self.alerts.check(_ic, _ts, _sq, _cs)
                    else:
                        # log("Updated call squawk", _sq)
                        flx.data['sq'] = _sq
                        self.alerts.check(_ic, _ts, _sq, _cs)

                if _cs is not None:
                    if flx.data['cs'] is not None:
                        if flx.data['cs'] != _cs:
                            new_fl = Flight(_ic, _ts, _sq, _cs, _alt)
                            # log("New flight from callsn", _cs, new_fl.data, new_fl.pos)
                            self.add(new_fl)
                            self.alerts.check(_ic, _ts, _sq, _cs)
                            return
                        else:
                            self.alerts.check(_ic, _ts, _sq, _cs)
                    else:
                        # log("Updated call sign", _cs)
                        flx.data['cs'] = _cs
                        self.alerts.check(_ic, _ts, _sq, _cs)

                _alt = int(_alt)
                if _alt != 0:
                    # Temptative filter to discard bad data
                    #  altitude >   300 feets
                    #  delta    < 30000 feets
                    if flx.pos['alt_ls'] == 0 or \
                            (_alt > 300 and abs(flx.pos['alt_ls'] - _alt) < 30000):
                        flx.pos['alt_ls'] = _alt

                        if flx.pos['alt_fs'] == 0:
                            flx.pos['alt_fs'] = _alt

                        if flx.pos['alt_min'] == 0 or flx.pos['alt_min'] > _alt:
                            flx.pos['alt_min'] = _alt

                        if flx.pos['alt_max'] == 0 or flx.pos['alt_max'] < _alt:
                            flx.pos['alt_max'] = _alt

                flx.data['ls'] = float(_ts)
                flx.data['nm'] = flx.data['nm'] + 1

                return

        try:
            new_fl = Flight(_ic, _ts, _sq, _cs, _alt)
            self.add(new_fl)
            # log("New flight", new_fl.data, new_fl.pos)
            self.alerts.check(_ic, _ts, _sq, _cs)

        except Exception as e:
            global cnt
            log("Exception:", e)
            log("         : Check input line {:10d}".format(cnt))


if __name__ == "__main__":

    def handler_alarm(_signum, _frame):
        global signal_alarm
        signal_alarm = 1

    global signal_alarm
    signal.signal(signal.SIGALRM, handler_alarm)
    signal_alarm = 0
    period_alarm = 3600
    signal.alarm(period_alarm)

    log("Running: Pid {:5d}".format(os.getpid()))

    fl = FlightList()

    global cnt
    cnt = 0
    last_ct = 0
    init_ts = time()
    last_ts = init_ts
    for line in sys.stdin:
        cnt = cnt + 1

        # log("Read", line, end='')
        cnt_alarm = 500000
        if cnt % cnt_alarm == 0 or signal_alarm == 1:
            signal_alarm = 0
            signal.alarm(period_alarm)

            dm = cnt - last_ct
            dt = time() - last_ts
            log("Running   : Processed {:>12,d} messages ({:5d} /s)"
                .format(cnt, int(dm/dt)))
            last_ct = cnt
            last_ts = time()

        words = line.split()
        if words[0] == "SQ":
            fl.addupd_flight(words[1], words[3], _sq=words[4])
        elif words[0] == "CS":
            fl.addupd_flight(words[1], words[3], _cs=words[5])
        elif words[0] == "FL":
            fl.addupd_flight(words[1], words[3], _alt=words[4])
        # log("\n")

    nmsgs = fl.print()

    if nmsgs != cnt:
        log("Terminated: Fail {:>12,d} cnt != {:>12,d} nmsgs"
            .format(cnt, nmsgs))

    log("Terminated: Processed {:>12,d} messages ({:5d} /s)"
        .format(cnt, int(cnt/(time() - init_ts))))

    sys.exit(0)
