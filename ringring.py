#! /usr/bin/env python3

# (c) Kazansky137 - Tue Dec 17 21:14:07 UTC 2019

import sys
import requests
from common import log, load_config


class RingRing():

    def __init__(self):
        self.params = {}
        load_config(self.params, "config/ringring.txt")
        return

    def send(self, _msg):
        values = {"apiKey":     self.params["apiKey"],
                  "to":         self.params["to"],
                  "message":    _msg
                  }
        r = requests.post("https://api.ringring.be/sms/sandbox/message",
                          json=values)
        log("Return code", r.status_code, r.json()['ResultDescription'])
        return


if __name__ == "__main__":

    rr = RingRing()

    rr.send("ADS-B ALERT: AABBCC: OO-SFU Brussels Airlines")

    sys.exit(0)
