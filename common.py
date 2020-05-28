#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 04:21:26 UTC 2020

import io
import os
import sys
import re
import math
from time import gmtime, strftime
from pyModeS import common
import pyModeS.extra.aero as aero
import argparse
import pprint


def log(*args, _ts=None, _col=None, _file=sys.stderr, **kwargs):
    if _ts is not None:
        _ts = gmtime(float(_ts))
    else:
        _ts = gmtime()
    prog = re.search("[a-z]+", sys.argv[0]).group()
    if _col is None:
        print("{:s} {:s}:".format(strftime("%d %H:%M:%S", _ts), prog),
              *args, **kwargs, file=_file)
    else:
        string_io = io.StringIO()
        print("{:s} {:s}:".format(strftime("%d %H:%M:%S", _ts), prog),
              file=string_io, end=' ')
        xt_set(*_col, _file=string_io)
        print(*args, **kwargs, end='', file=string_io)

        # /AKN - Tue Dec 10 22:22:26 CET 2019
        # 1. Line padding in case of colored output should be moved
        #    to xt_.... functions.
        # 2. Should truncate line to xt_line_max
        global xt_line_del, xt_line_max     # See comment AKN below
        xt_line_pad = xt_line_max - (len(string_io.getvalue()) - xt_line_del)
        print(xt_line_pad * ' ', end='', file=string_io)
        print(string_io.getvalue(), end='', file=_file)
        string_io.close()

        xt_reset(_file=_file)
    _file.flush()


def load(_class, _filename, _type):
    cnt = 0
    with open(_filename, 'r') as f:
        for l in f.readlines():
            l, s, t = l.partition('#')      # main inline/outline comment sep.
            x = l.strip(" \n\t")
            if len(x) == 0 or x[0] in ";":  # ';' secondary outline comment
                continue
            _class.add(_type(*tuple(w.strip() for w in x.split(':'))))
            cnt = cnt + 1
        f.close()
    return cnt


def load_config(_dict, _filename):
    cnt = 0
    with open(_filename, 'r') as f:
        for l in f.readlines():
            l, s, t = l.partition('#')      # main inline/outline comment sep.
            x = l.strip(" \n\t")
            if len(x) == 0 or x[0] in ";":  # ';' secondary outline comment
                continue
            k, v = x.split(':')
            _dict[k.strip(' ')] = v.strip(' ')
            cnt = cnt + 1
        f.close()

        parser = argparse.ArgumentParser()

        parser.add_argument("-d", "--debug", action="store_true",
                            help="debug mode (default off)")
        parser.add_argument("-f", "--file",  action="store_true",
                            help="file mode (default off)")
        parser.add_argument("-a", "--alerts", action="store_true",
                            help="manage alerts (default on)")
        parser.add_argument("--noalerts", action="store_true",
                            help="do not manage alerts")
        parser.add_argument("-s", "--sms", action="store_true",
                            help="send sms for urgent alert (default on)")
        parser.add_argument("--nosms", action="store_true",
                            help="do not send sms for urg. alert")
        parser.add_argument("-m", "--mail", action="store_true",
                            help="send mail for urgent alert (default on)")
        parser.add_argument("--nomail", action="store_true",
                            help="do not send mail for urg. alert")
        parser.add_argument("--profile", type=str,
                            help="dump profile data to file")

        args = parser.parse_args()
        _dict["arg_debug"] = args.debug

        # Default values
        # debug   = False
        # file    = False (if True sms/mail/alerts = False, can be overwritten)
        # sms     = True
        # mail    = True
        # alerts  = True
        # profile = None
        if not args.file:
            _dict["arg_sms"]    = True if not args.nosms    else False
            _dict["arg_mail"]   = True if not args.nomail   else False
            _dict["arg_alerts"] = True if not args.noalerts else False
        else:
            _dict["arg_sms"]    = False if not args.sms    else True
            _dict["arg_mail"]   = False if not args.mail   else True
            _dict["arg_alerts"] = False if not args.alerts else True
        _dict["arg_profile"] = args.profile

    return cnt


def print_config(_dict):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_dict)


def xt_color_table():
    for style in range(8):
        for fg in range(30, 38):
            s1 = ''
            for bg in range(40, 48):
                format = ';'.join([str(style), str(fg), str(bg)])
                s1 += '\x1b[%sm %s \x1b[0m' % (format, format)
            print(s1)
        print('\n')


xt_colors = {'black': 0, 'red': 1, 'green': 2, 'yellow': 3,
             'blue': 4, 'magenta': 5, 'cyan': 6, 'white': 7
             }

xt_effects = {'end': 0, 'bold': 1, 'disable': 2, 'italic': 3,
              'underline': 4, 'blink': 5, 'blink2': 6, 'reverse': 7,
              'invisible': 8, 'strikethrough': 9
              }


def xt_set(_fg='black', _bg=None, _st=None, _file=sys.stdout):
    global xt_line_del, xt_line_max

    try:
        xt_line_del
    except NameError:
        xt_line_del = 0

    try:
        xt_line_max = int(os.environ['TERM_COLS'])
    except KeyError:
        xt_line_max = 120

    c_fg = 30 + xt_colors[_fg]
    if _bg is None and _st is None:             # FG
        print("\033[0;{:d}m".format(c_fg), end='', file=_file)
        xt_line_del = xt_line_del + 7
    else:
        c_bg = 40 + xt_colors[_bg]
        if _st is None:                         # FG BG
            print("\033[0;{:d};{:d}m".format(c_fg, c_bg), end='', file=_file)
            xt_line_del = xt_line_del + 10
        else:                                    # FG BG ST
            c_st = xt_effects[_st]
            print("\033[{:d};{:d};{:d}m".format(c_st, c_fg, c_bg),
                  end='', file=_file)
            xt_line_del = xt_line_del + 10
    return


def xt_reset(_file=sys.stdout):
    global xt_line_del
    print("\033[0m", file=_file)
    xt_line_del = 0
    return


def adsb_ca(_msg):
    dfbin = common.hex2bin(_msg[:2])
    return common.bin2int(dfbin[5:8])


def distance(lat1, long1, lat2, long2):
    dist = aero.distance(lat1, long1, lat2, long2)
    return dist/1852.0


def bearing(lat1, lon1, lat2, lon2):
    return aero.bearing(lat1, lon1, lat2, lon2)


if __name__ == "__main__":

    """
    xt_set()
    print("FG default", end='')
    xt_reset()

    xt_set('green')
    print("FG green", end='')
    xt_reset()

    xt_set('red', _st='blink', _bg='yellow')
    print("FG red BG yellow", end='')
    xt_reset()

    xt_set('magenta', 'cyan', 'disable')
    print("FG magenta BG cyan", end='')
    xt_reset()
    """

    """
    xt_color_table()
    """

    config = {}
    load_config(config, "config/config.txt")
    print_config(config)

    sys.exit(0)
