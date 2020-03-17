#! /usr/bin/env python3

# (c) Kazansky137 - Tue Mar 17 18:03:25 UTC 2020

import sys
import requests
from common import log, load_config


class RingRing():

    def __init__(self):
        self.params = {}
        load_config(self.params, "config/ringring.txt")
        return

    def send(self, _msg):
        _msg = self.params["prefix"] + " \n" + _msg
        values = {"apiKey":     self.params["apiKey"],
                  "to":         self.params["to"],
                  "message":    _msg
                  }
        r = requests.post("https://api.ringring.be/sms/v1/message",
                          json=values)
        log("Return code", r.status_code, r.json()['ResultDescription'])
        return

    def phone(self):
        return self.params["to"]


if __name__ == "__main__":

    rr = RingRing()

    rr.send("44CCD5\nOO-SFU Brussels Airlines")

    sys.exit(0)
