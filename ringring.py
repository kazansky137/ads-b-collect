#! /usr/bin/env python3

# (c) Kazansky137 - Tue May 12 21:29:57 UTC 2020

import sys
import requests
from common import log, load_config


class RingRing():

    def __init__(self):
        self.params = {}
        load_config(self.params, "config/config.txt")
        return

    def send(self, _msg):
        if self.params["arg_sms"] is False:
            return
        _msg = self.params["pref"] + " " + _msg
        values = {"apiKey":     self.params["apiKey"],
                  "to":         self.params["phone"],
                  "message":    _msg
                  }
        r = requests.post("https://api.ringring.be/sms/v1/message",
                          json=values)
        log("Return code", r.status_code, r.json()['ResultDescription'])
        return

    def phone(self):
        return self.params["phone"]


if __name__ == "__main__":

    rr = RingRing()

    rr.send("44CCD5\nOO-SFU Brussels Airlines")

    sys.exit(0)
