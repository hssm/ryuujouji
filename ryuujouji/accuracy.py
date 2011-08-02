# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
import solver


aligned_path  = os.path.join('dbs/eval-alignment.data')
f = open(aligned_path)

correct = 0
incorrect = 0

for line in f:
    line = line.strip()
    line = unicode(line)
    (word, reading_full, align) = line.split(' ')
    
    
    (full_reading, graphemes) = reading_full.split(':')
    graphemes = graphemes.split('|')
    alignments = align.split('|')
    word = unicode(word)
    
    solveObject = solver.getSolver(word, full_reading)
    solution = solveObject.get_solution()
    
    is_correct = True
#    print "Word:", word, "--", full_reading
#    print "Graphemes:"
    
    if solution is not None:
        for (i, (graph, sol)) in enumerate(zip(graphemes, solution)):
#            print '  %s[%s] -- %s[%s]' % (graph, alignments[i],
#                                          sol.grapheme, sol.reading)
            if not (graph == sol.grapheme and alignments[i] == sol.reading):
                is_correct = False
    else:
        is_correct = False
        
    if not is_correct:
        incorrect += 1
        
        
        if solution is not None:
            print "---------------------------"
            print line
            print "My solution(s):"
            solutions = solveObject.get_all_solutions()
            for sol in solutions:
                print "Solution #:"
                for s in sol:
                    print "           %s %s" % (s.grapheme, s.reading)
            print "---------------------------"
        else:
            print line

    else:
        correct += 1
        
print "Total correct =", correct
print "Total incorrect=", incorrect
total_words = correct + incorrect
percentage = 100 * float(correct)/total_words
print "Percentage correct=", percentage