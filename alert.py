#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 20:49:27 UTC 2020

from common import log, load, distance, bearing, load_config
import sys
import sendmail
import ringring
import importlib

flightlist = importlib.import_module("flights-2-txt")
params     = {}
load_config(params, "config/config.txt")


alert_cat = {'urg': ('yellow', 'red', 'blink'),
             'mil': ('red', 'green', 'bold'),
             'bru': ('blue', 'yellow', 'bold'),
             'civ': ('blue', 'white', 'bold'),
             'gav': ('red', 'black', 'bold'),
             'exc': ('black', 'white', 'italic')
             }


class Alert():

    def __init__(self, _cat, _trigger, _val, _com=None, _validity=3600):
        self.mail = sendmail.SendMail()
        self.ring = ringring.RingRing()
        self.alert = (_cat, _trigger, _val, _com, int(_validity))
        self.fs = 0

    def print(self, _file=sys.stdout):
        print(self.alert, self.fs, file=_file)

    def message(self):
        return str(self.alert)

    def log(self, _ts, _ic, _alt, _dist, _bear, _file=sys.stderr):
        tail = flightlist.FlightList.codes.tail(_ic)
        _alt, _dist, _bear = int(_alt), float(_dist), float(_bear)
        fmt = "{:6s} : {:8s} : {:5d} {:5.1f} {:5.1f}°"
        self.mail.send(fmt.format(_ic, tail, _alt, _dist, _bear),
                       self.message())
        fmt = "{:6s} : {:8s} : {:5d} {:5.1f} {:5.1f}° {:s}"
        log(fmt.format(_ic, tail, _alt, _dist, _bear, self.message()),
            _ts=_ts, _file=_file, _col=alert_cat[self.alert[0]])
        if self.alert[0] == "urg":
            if _alt > 4000:  # Typical transition altitude
                fl = int(_alt/100)
                self.ring.send("{:s} {:s}\nFL{:d} {:5.1f} {:5.1f}°\n{:s}"
                               .format(_ic, tail, fl, _dist, _bear,
                                       self.alert[3]))
            else:
                self.ring.send("{:s} {:s}\n{:5d} {:5.1f} {:5.1f}°\n{:s}"
                               .format(_ic, tail, _alt, _dist, _bear,
                                       self.alert[3]))


class AlertList():

    def addpermanent(self):
        self.add(Alert('urg', 'sq', '7700', "General Emergency", 60))

    def __init__(self):
        self.list = []
        self.addpermanent()
        cnt = load(self, "config/alerts.txt", Alert)
        log("Loaded {:3d} alerts".format(cnt))

    def reload(self):
        log("Clearing alerts")
        self.list.clear()
        log("Done")
        self.addpermanent()
        cnt = load(self, "config/alerts.txt", Alert)
        log("Loaded {:3d} alerts".format(cnt))

    def add(self, _alert):
        self.list.append(_alert)

    def print(self, _file=sys.stdout):
        for alert in self.list:
            alert.print(_file=_file)

    def check(self, fl):
        if params["arg_alerts"] is False:
            return
        # log("Check Flight ", fl.data, fl.pos)
        # Alert delayed waiting for position or least 16 messages
        if fl.data['nm'] < 16:
            if fl.pos['alt_ls'] == 0:
                return None
            if fl.pos['lat_ls'] == 0.0 and fl.pos['long_ls']:
                return None

        for alert in self.list:
            # log("Check alert",alert.message())
            if fl.data['ls'] - alert.fs < alert.alert[4]:
                continue
            if((alert.alert[1] == 'ic' and alert.alert[2] == fl.data['ic']) or
               (alert.alert[1] == 'sq' and alert.alert[2] == fl.data['sq']) or
               (alert.alert[1] == 'cs' and alert.alert[2] == fl.data['cs'])):
                alert.fs = fl.data['ls']
                # log("Matching   ", alert.message())
                lat_ref = float(params["lat"])
                long_ref = float(params["long"])
                if fl.pos['lat_ls'] != 0.0 and fl.pos['long_ls'] != 0.0:
                    dist = distance(fl.pos['lat_ls'],
                                    fl.pos['long_ls'], lat_ref, long_ref)
                    bear = bearing(lat_ref, long_ref, fl.pos['lat_ls'],
                                   fl.pos['long_ls'])
                else:
                    dist = bear = 0.0
                alert.log(fl.data['ls'], fl.data['ic'],
                          fl.pos['alt_ls'], dist, bear)
                return alert
        return None


if __name__ == "__main__":

    """
    alert_list = AlertList()
    alert_list.print()
    alert_list.check('IC0001',0,None,None)
    alert_list.check('IC0002',0,'SQ0002',None)
    alert_list.check('IC0003',0,None,'CS0003')
    alert_list.check('IC0004',0,None,'CS0004')
    """

    """
    log("Alert Std")
    log("Alert Urg", _col=alert_cat['urg'])
    log("Alert Mil", _col=alert_cat['mil'])
    log("Alert Bru", _col=alert_cat['bru'])
    log("Alert Civ", _col=alert_cat['civ'])
    log("Alert Gav", _col=alert_cat['gav'])
    log("Alert Exc", _col=alert_cat['exc'])
    """

    sys.exit(0)
