# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import MeCab
import sys
import string

sentence = "ヨウ素１３１"

try:

    print MeCab.VERSION

    t = MeCab.Tagger (" ".join(sys.argv))

    print t.parse (sentence)

    m = t.parseToNode (sentence)
    while m:
        print m.surface, "\t", m.feature
        m = m.next
    print "EOS"

    n = t.parseToNode(sentence)
    len = n.sentence_length;
    for i in range(len + 1):
        b = n.begin_node_list(i)
        e = n.end_node_list(i)
        while b:
            print "B[%d] %s\t%s" % (i, b.surface, b.feature)
            b = b.bnext 
        while e:
            print "E[%d] %s\t%s" % (i, e.surface, e.feature)
            e = e.bnext 
    print "EOS";

    d = t.dictionary_info()
    while d:
        print "filename: %s" % d.filename
        print "charset: %s" %  d.charset
        print "size: %d" %  d.size
        print "type: %d" %  d.type
        print "lsize: %d" %  d.lsize
        print "rsize: %d" %  d.rsize
        print "version: %d" %  d.version
        d = d.next

except RuntimeError, e:
    print "RuntimeError:", e;

