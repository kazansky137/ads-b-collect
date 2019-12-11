#! /usr/bin/env python3

# (c) Kazansky137 - Wed Dec 11 11:42:02 CET 2019

from common import log, load
import sys

alert_cat = {'emg': ('yellow', 'red', 'blink'),
             'mil': ('red', 'green', 'bold'),
             'bru': ('blue', 'yellow', 'bold'),
             'civ': ('blue', 'white', 'bold'),
             'gav': ('red', 'black', 'bold'),
             'exc': ('black', 'white', 'italic')
             }


class Alert():

    def __init__(self, _cat, _trigger, _val, _com=None, _validity=3600):
        self.alert = (_cat, _trigger, _val, _com, int(_validity))
        self.fs = 0

    def print(self, _file=sys.stdout):
        print(self.alert, self.fs, file=_file)

    def message(self):
        return str(self.alert)

    def log(self, _ts, _file=sys.stderr):
        log("Alert {:s}".format(self.message()),
            _ts=_ts, _file=_file, _col=alert_cat[self.alert[0]])


class AlertList():

    def addpermanent(self):
        self.add(Alert('emg', 'sq', '7700', "General Emergency", 60))

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

    def check(self, _ic, _ts, _sq, _cs):
        # log("Check Flight ", _ic, _ts, _sq, _cs)
        for alert in self.list:
            # log("Check alert",alert.message())
            if float(_ts) - float(alert.fs) < alert.alert[4]:
                continue
            if((alert.alert[1] == 'ic' and alert.alert[2] == _ic) or
               (alert.alert[1] == 'sq' and alert.alert[2] == _sq) or
               (alert.alert[1] == 'cs' and alert.alert[2] == _cs)):
                alert.fs = _ts
                # log("Matching   ",alert.message())
                return alert
        return None

if __name__ == "__main__":

    """
    alert_list = AlertList()
    alert_list.print()
    """

    """
    log("Alert Std")
    log("Alert Emg", _col=alert_cat['emg'])
    log("Alert Mil", _col=alert_cat['mil'])
    log("Alert Bru", _col=alert_cat['bru'])
    log("Alert Civ", _col=alert_cat['civ'])
    log("Alert Gav", _col=alert_cat['gav'])
    log("Alert Exc", _col=alert_cat['exc'])
    """

    sys.exit(0)
