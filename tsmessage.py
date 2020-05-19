#! /usr/bin/env python3

# (c) Kazansky137 - Tue May 19 17:33:30 UTC 2020

from common import log, load_config

_init_done = False
_debug     = 0


class TsMessage():
    def __init__(self, _ts, _msg):
        global _init_done
        if not _init_done:
            self.params = {}
            load_config(self.params, "config/config.txt")
            global _debug
            _debug = 1 if self.params["arg_debug"] else 0
            _init_done = True

        self.ts = float(_ts)
        self.msg = _msg
        self.adsb = {}
        self.adsb['ts'] = _ts
        return

    def disc(self, _dict):
        self.adsb.update(_dict)

    def print_raw(self):
        print("{:20.9f} {:s}".format(self.ts, self.msg), flush=True)

    def print(self):
        print(self.adsb)

    def print_legacy(self):
        ts = self.ts
        msg = self.msg
        icao = self.adsb['ic']
        type = self.adsb['type']

        if type == "CS":
            ca = self.adsb['ca']
            cs = self.adsb['cs']
            print("{:3s} {:15.9f} {:s} {:s} {:s} {:s}".format
                  ("CS", ts, msg, icao, ca, cs), flush=True)
        elif type == "LB":
            alt = self.adsb['altb']
            lat = self.adsb['lat']
            long = self.adsb['long']
            fmt = "{:3s} {:15.9f} {:s} {:s} {:d} {:9.5f} {:9.5f}"
            print(fmt.format
                  ("LB", ts, msg, icao, alt, lat, long), flush=True)
        elif type == "VH":
            speed = self.adsb['speed']
            head = self.adsb['head']
            rocd = self.adsb['rocd']
            if _debug:
                log("debug VH:", speed, head, rocd)
            fmt = "{:3s} {:15.9f} {:s} {:s} {:d} {:5.1f} {:d}"
            print(fmt.format
                  ("VH", ts, msg, icao, speed, head, rocd), flush=True)
        elif type == "LG":
            alt = self.adsb['altg']
            lat = self.adsb['lat']
            long = self.adsb['long']
            fmt = "{:3s} {:15.9f} {:s} {:s} {:d} {:9.5f} {:9.5f}"
            print(fmt.format
                  ("LG", ts, msg, icao, alt, lat, long), flush=True)
        elif type == "SQ":
            sq = self.adsb['sq']
            print("{:3s} {:15.9f} {:s} {:s} {:s}".format
                  ("SQ", ts, msg, icao, sq), flush=True)
        elif type == "AL":
            alt = self.adsb['alt']
            print("{:3s} {:15.9f} {:s} {:s} {:d}".format
                  ("AL", ts, msg, icao, alt), flush=True)
