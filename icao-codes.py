#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 20:49:27 UTC 2020

import sys
import requests
from common import log, load_config

codes = {}
load_config(codes, "config/icao-tail.txt")


class IcaoCodes():

    def __init__(self):
        return

    def tail(self, _ic):
        try:
            tail = codes[_ic]
        except Exception as e:
            tail = "______"
        return tail

    def print(self):
        for k in codes:
            print(k, codes[k])


if __name__ == "__main__":

    icl = IcaoCodes()

    icl.print()

    print(icl.tail("448442"))

    print(icl.tail("X48442"))

    sys.exit(0)
