# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import argparse

parser = argparse.ArgumentParser(description='Find reading segments.')
parser.add_argument('-f', type = argparse.FileType('r'), default = '-')
parser.add_argument('--encoding', default='utf-8')
parser.add_argument('-d', '--delimiter', default=u' ')
args = parser.parse_args()

from solver import Solver

try:
    
    for i, line in enumerate(args.f):
        line = unicode(line, encoding = args.encoding)
        line = line.rstrip()
        try:
            word, reading = line.split(args.delimiter, 1)
            s = Solver(word, reading)
            s.print_segments()
            print
        except ValueError, e:
            print "Line %d: Cannot parse line -- [%s]" % (i, line)
        
except KeyboardInterrupt:
    pass