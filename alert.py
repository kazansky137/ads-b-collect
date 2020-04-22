#! /usr/bin/env python3

# (c) Kazansky137 - Wed Apr 22 18:04:12 UTC 2020

from common import log, load, distance, bearing
import sys
import sendmail
import ringring
import importlib
flightlist = importlib.import_module("flights-2-txt")

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
        fmt = "Alert: {:s} : {:s} : {:5d}"
        self.mail.send(fmt.format(_ic, tail, _alt), self.message())
        fmt = "Alert: {:s} : {:s} : {:5d} {:5.1f} {:5.1f}° {:s}"
        log(fmt.format(_ic, tail, _alt, _dist, _bear, self.message()),
            _ts=_ts, _file=_file, _col=alert_cat[self.alert[0]])
        if self.alert[0] == "urg":
            if _alt > 4000:  # Typical transition altitude
                fl = int(_alt/100)
                self.ring.send("{:s} {:s} FL{:d} {:5.1f} {:5.1f}°\n{:s}"
                               .format(_ic, tail, fl, _dist, _bear,
                                       self.alert[3]))
            else:
                self.ring.send("{:s} {:s} {:5d} {:5.1f} {:5.1f}°\n{:s}"
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

    def check(self, _ic, _ts, _sq, _cs, _alt, _lat, _long):
        # Alert delayed waiting for altitude and position
        if _alt == 0:
            return None
        if _lat == 0.0 and _long == 0.0:
            return None
        # log("Check Flight ", _ic, _ts, _sq, _cs, _alt)
        for alert in self.list:
            # log("Check alert",alert.message())
            if float(_ts) - float(alert.fs) < alert.alert[4]:
                continue
            if((alert.alert[1] == 'ic' and alert.alert[2] == _ic) or
               (alert.alert[1] == 'sq' and alert.alert[2] == _sq) or
               (alert.alert[1] == 'cs' and alert.alert[2] == _cs)):
                alert.fs = _ts
                # log("Matching   ", alert.message())
                dist = distance(_lat, _long, 50.55413, 4.68801)
                bear = bearing(_lat, _long, 50.55413, 4.68801)
                alert.log(_ts, _ic, _alt, dist, bear)
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
