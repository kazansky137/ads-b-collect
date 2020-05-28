#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 20:49:27 UTC 2020

import alert
from common import log, distance, bearing, load_config
import sys
import os
import signal
from time import gmtime, strftime, time
import importlib
import traceback
import cProfile
icaocodes = importlib.import_module("icao-codes")


class Flight():

    def __init__(self, _ic, _ts, _sq=None, _cs=None,
                 _alt='0', _lat='0', _long='0',
                 _speed='0', _head='0', _rocd='0'):

        self.data = {'ic': _ic,         # Icao hex code
                     'fs': float(_ts),  # First seen
                     'ls': float(_ts),  # Last seen
                     'sq': _sq,         # Squawk
                     'cs': _cs,         # Call sign
                     'nm': 1}           # Number of messages

        self.pos = {'alt_fs': int(_alt),      # Altitude  first seen
                    'alt_ls': int(_alt),      # "         last seen
                    'alt_min': int(_alt),     # "         minimum
                    'alt_max': int(_alt),     # "         maximum
                    'lat_ls': float(_lat),    # Latitude  last seen
                    'long_ls': float(_long),  # Longitude last seen
                    'speed_ls': int(_speed),  # Speed     last seen
                    'head_ls': float(_head),  # heading   last seen
                    'rocd_ls': int(_rocd)}    # Rate C/D  last seen

    def print(self, _file=sys.stdout):
        if _file == sys.stderr and (self.data['nm'] < 16 or
           (time() - self.data['ls']) > 120):
            return

        lat_ref = float(params["lat"])
        long_ref = float(params["long"])
        dist = 0.0
        bear = 0.0
        if self.pos['lat_ls'] != 0.0 and self.pos['long_ls'] != 0.0:
            dist = distance(self.pos['lat_ls'], self.pos['long_ls'],
                            lat_ref, long_ref)
            bear = bearing(lat_ref, long_ref, self.pos['lat_ls'],
                           self.pos['long_ls'])
        fmt = "{:s} " * 4 + "{:>8s} {:5d} {:7.1f}" + 4 * " {:5d}" + \
              " {:9.5f} {:9.5f} {:5.1f} {:5.1f}° {:5.1f}°"
        print(fmt.format(strftime("%d %H:%M:%S", gmtime(self.data['fs'])),
              strftime("%d %H:%M:%S", gmtime(self.data['ls'])),
              self.data['ic'], str(self.data['sq']),
              str(self.data['cs']), self.data['nm'],
              self.data['ls'] - self.data['fs'],
              self.pos['alt_fs'], self.pos['alt_ls'],
              self.pos['alt_min'], self.pos['alt_max'],
              self.pos['lat_ls'], self.pos['long_ls'],
              dist, bear, self.pos['head_ls']), file=_file)

    def __lt__(self, other):
        # Order by last seen
        # If equal order by first seen
        s_ls, o_ls = gmtime(self.data['ls']), gmtime(other.data['ls'])
        if s_ls == o_ls:
            s_fs, o_fs = gmtime(self.data['fs']), gmtime(other.data['fs'])
            val = s_fs < o_fs
        else:
            val = s_ls < o_ls
        return val


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
        for flx in sorted(self.list):
            flx.print(_file)
            cnt = cnt + flx.data['nm']
        return cnt

    def addupd_flight(self, _ts, _ic, _sq=None, _cs=None,
                      _alt='0', _lat='0', _long='0',
                      _speed='0', _head='0', _rocd='0'):
        if self.signal_hup == 1:
            self.signal_hup = 0
            self.alerts.reload()
            self.print(_file=sys.stderr)
            sys.stderr.flush()

        if _ic == '000000':
            return

        for flx in self.list:
            if flx.data['ic'] == _ic:
                # log("Existing flight for icao",
                #     _ic, flx.data['sq'], flx.data['cs'],
                #     flx.pos['alt_ls'], flx.data['nm'])

                if _sq is not None:
                    if flx.data['sq'] is not None:
                        if flx.data['sq'] != _sq:
                            new_fl = Flight(_ic, _ts, _sq, _cs,
                                            _alt, _lat, _long)
                            # log("New flight from squawk",
                            #     _sq, new_fl.data, new_fl.pos)
                            self.alerts.check(new_fl)
                            self.add(new_fl)
                            return
                    else:
                        flx.data['sq'] = _sq
                        # log("Add SQ ", flx.data, flx.pos)

                if _cs is not None:
                    if flx.data['cs'] is not None:
                        if flx.data['cs'] != _cs:
                            new_fl = Flight(_ic, _ts, _sq, _cs,
                                            _alt, _lat, _long)
                            # log("New flight from callsn", _cs,
                            #     new_fl.data, new_fl.pos)
                            self.alerts.check(new_fl)
                            self.add(new_fl)
                            return
                    else:
                        flx.data['cs'] = _cs
                        # log("Add CS ", flx.data, flx.pos)

                # Altitude change do not create flights
                #   Update if alt_ls change detected
                _alt = int(_alt)
                if _alt != 0 and flx.pos['alt_ls'] != _alt:
                    # Should base test on a sliding mean window !!
                    # Temptative filter to discard bad data
                    #  altitude >   300 feets
                    #  altitude < 60000 feets (Concorde)
                    #  delta    < 10000 feets
                    if flx.pos['alt_ls'] == 0 or \
                            (_alt > 300 and _alt < 60000 and
                             abs(flx.pos['alt_ls'] - _alt) < 10000):
                        flx.pos['alt_ls'] = _alt

                        if flx.pos['alt_fs'] == 0:
                            flx.pos['alt_fs'] = _alt

                        if flx.pos['alt_min'] == 0 or \
                                flx.pos['alt_min'] > _alt:
                            flx.pos['alt_min'] = _alt

                        if flx.pos['alt_max'] == 0 or \
                                flx.pos['alt_max'] < _alt:
                            flx.pos['alt_max'] = _alt
                        # log("Update ALT", flx.data, flx.pos)

                # Position change do not create flights
                #   Update permanently
                if _lat != '0' and _long != '0':
                    flx.pos['lat_ls'] = float(_lat)
                    flx.pos['long_ls'] = float(_long)
                    # log("Update POS", flx.data, flx.pos)

                # Velocity change do not create flights
                #   Update permanently
                if _head != '0':
                    flx.pos['head_ls'] = float(_head)

                flx.data['ls'] = float(_ts)
                flx.data['nm'] = flx.data['nm'] + 1

                self.alerts.check(flx)

                return

        try:
            new_fl = Flight(_ic, _ts, _sq, _cs, _alt, _lat, _long)
            self.add(new_fl)
            # log("New flight", new_fl.data, new_fl.pos)
            self.alerts.check(new_fl)

        except Exception as e:
            global cnt
            log("Exception:", e)
            log("         : Check input line {:10d}".format(cnt))
            log(traceback.format_exc())


if __name__ == "__main__":

    params = {}
    load_config(params, "config/config.txt")

    if params["arg_profile"]:
        log("Profiling On")
        pr = cProfile.Profile()
        pr.enable()

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
        try:
            if words[0] == "SQ":
                fl.addupd_flight(words[1], words[3], _sq=words[4])
            elif words[0] == "CS":
                fl.addupd_flight(words[1], words[3], _cs=words[5])
            elif words[0] == "AL":
                fl.addupd_flight(words[1], words[3], _alt=words[4])
            elif words[0] in ["LB", "LG"]:
                fl.addupd_flight(words[1], words[3], _alt=words[4],
                                 _lat=words[5], _long=words[6])
            elif words[0] == "VH":
                fl.addupd_flight(words[1], words[3], _speed=words[4],
                                 _head=words[5], _rocd=words[6])

        except Exception as e:
            log("Exception:", e)
            log(words)
            log(line)

        # log("\n")

    nmsgs = fl.print()

    if nmsgs != cnt:
        log("Terminated: Warning {:>12,d} cnt != {:>12,d} nmsgs"
            .format(cnt, nmsgs))

    log("Terminated: Processed {:>12,d} messages ({:5d} /s)"
        .format(cnt, int(cnt/(time() - init_ts))))

    if params["arg_profile"]:
        pr.disable()
        pr.dump_stats(params["arg_profile"])

    sys.exit(0)
