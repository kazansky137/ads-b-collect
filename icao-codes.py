#! /usr/bin/env python3

# (c) Kazansky137 - Tue Mar 17 18:03:25 UTC 2020

import sys
import requests
from common import log, load_config


class IcaoCodes():

    def __init__(self):
        self.codes = {}
        load_config(self.codes, "config/icao-tail.txt")
        return

    def tail(self, _ic):
        try:
            tail = self.codes[_ic]
        except Exception as e:
            tail = "______"
        return tail

    def print(self):
        for k in self.codes:
            print(k, self.codes[k])


if __name__ == "__main__":

    icl = IcaoCodes()

    icl.print()

    print(icl.tail("448442"))

    print(icl.tail("X48442"))

    sys.exit(0)
