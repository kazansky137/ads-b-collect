#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 04:21:26 UTC 2020

import argparse
import sys, pstats

parser = argparse.ArgumentParser()
group  = parser.add_mutually_exclusive_group()

group.add_argument("-c", "--cumulative", action="store_true",
                   help="sort by cumulative time (default)")

group.add_argument("-t", "--tottime", action="store_true",
                   help="sort by internal time")

group.add_argument("-n", "--calls", action="store_true",
                   help="sort by call count")

parser.add_argument("-d", "--dir", action="store_false",
                    help="show dir")

parser.add_argument("-l", "--lines", type=int, default=11,
                    help="number of lines to show")

parser.add_argument('infile', nargs=argparse.REMAINDER, help="profiler file")

args = parser.parse_args()

if args.tottime:
    sort = 'tottime'
elif args.calls:
    sort = 'calls'
else:
    sort = 'cumulative'

if len(args.infile) != 1:
    print("Missing input profile file")
    sys.exit(1)

p = pstats.Stats(args.infile[0])

if args.dir:
    p.strip_dirs().sort_stats(sort).print_stats(args.lines)
else:
    p.sort_stats(sort).print_stats(args.lines)

sys.exit(0)
