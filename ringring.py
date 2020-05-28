#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 20:49:27 UTC 2020

import sys
import requests
from common import log, load_config

params = {}
load_config(params, "config/config.txt")


class RingRing():

    def __init__(self):
        return

    def send(self, _msg):
        if params["arg_sms"] is False:
            return
        _msg = params["pref"] + " " + _msg
        values = {"apiKey":     params["apiKey"],
                  "to":         params["phone"],
                  "message":    _msg
                  }
        r = requests.post("https://api.ringring.be/sms/v1/message",
                          json=values)
        log("Return code", r.status_code, r.json()['ResultDescription'])
        return

    def phone(self):
        return params["phone"]


if __name__ == "__main__":

    rr = RingRing()

    rr.send("44CCD5\nOO-SFU Brussels Airlines")

    sys.exit(0)
