# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import argparse
import codecs
import sys

parser = argparse.ArgumentParser(description='Find reading segments.')
parser.add_argument('-i', default="-")
parser.add_argument('-o', '--output', default="-")
#parser.add_argument('-c', '--char-only', default=False)
parser.add_argument('--encoding', default='utf8')
parser.add_argument('-d', '--delimiter', default=u' ')
args = parser.parse_args()

import solver

try:
    if args.i == '-':
        infile = codecs.getreader(args.encoding)(sys.stdin)
    else:
        infile = codecs.open(args.i, 'r', args.encoding)
    
    if args.output == '-':
        outfile = codecs.getwriter(args.encoding)(sys.stdout)
    else:
        outfile = codecs.open(args.output, 'w', args.encoding)
    
    errfile = codecs.getwriter(args.encoding)(sys.stderr)
    
    success = 0
    fail = 0
    
    for i, line in enumerate(infile):
        line = line.encode(args.encoding)
        line = unicode(line, encoding = args.encoding)
        line = line.rstrip()
        try:
            word, reading = line.split(args.delimiter, 1)
            s = solver.print_segments_to_file(word, reading, outfile)
            outfile.write('\n')
            success = success + 1
        except ValueError, e:
            error = "Error on line %d: %s: %s" % (i+1, e.message, line)
            errfile.write(error+'\n')
            fail = fail + 1

    print "Processed %d lines successfully" % success
    if fail > 0:
        print "Failed on %d lines" % fail
        
except KeyboardInterrupt:
    pass