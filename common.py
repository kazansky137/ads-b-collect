#! /usr/bin/env python3

# (c) Kazansky137 - Sat Dec  7 22:53:15 CET 2019

import sys
from time import gmtime, strftime


def log(*args, _ts=None, _col=None, _file=sys.stderr, **kwargs):
    if _ts is not None:
        _ts = gmtime(float(_ts))
    else:
        _ts = gmtime()
    if _col is None:
        print("{:s} {:s}:".format(strftime("%d %H:%M:%S", _ts), sys.argv[0]),
              *args, **kwargs, file=_file)
    else:
        print("{:s} {:s}:".format(strftime("%d %H:%M:%S", _ts), sys.argv[0]),
              file=_file, end=' ')
        xt_set(*_col, _file=_file)
        print(*args, **kwargs, end='', file=_file)
        xt_reset(_file=_file)
    _file.flush()


def load(_class, _filename, _type):
    cnt = 0
    with open(_filename, 'r') as f:
        for l in f.readlines():
            l, s, t = l.partition('#')      # main inline/outline comment sep.
            l = l.strip(" \n\t")
            if len(l) == 0 or l[0] in ";":  # ';' secondary outline comment
                continue
            _class.add(_type(*tuple(w.strip() for w in l.split(':'))))
            cnt = cnt + 1
        f.close()
    return cnt


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
    c_fg = 30 + xt_colors[_fg]
    if _bg is None and _st is None:             # FG
        print("\033[0;{:d}m".format(c_fg), end='', file=_file)
    else:
        c_bg = 40 + xt_colors[_bg]
        if _st is None:                         # FG BG
            print("\033[0;{:d};{:d}m".format(c_fg, c_bg), end='', file=_file)
        else:                                    # FG BG ST
            c_st = xt_effects[_st]
            print("\033[{:d};{:d};{:d}m".format(c_st, c_fg, c_bg),
                  end='', file=_file)

    return


def xt_reset(_file=sys.stdout):
    print("\033[0m", file=_file)
    return

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

    sys.exit(0)
