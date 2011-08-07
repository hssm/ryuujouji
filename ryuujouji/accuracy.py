# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
import solver
import sqlite3

aligned_path  = os.path.join('dbs/eval-alignment.data')
f = open(aligned_path)

def save(conn):
    correct = 0
    incorrect = 0

    line_num = 0
    for line in f:
        line_num += 1
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
            
            ins = 'insert into line(line, correct) values(?,?)'
            conn.execute(ins, [line_num, False])
        else:
            correct += 1
            ins = 'insert into line(line, correct) values(?,?)'
            conn.execute(ins, [line_num, True])
    conn.commit()
    print "Total correct =", correct
    print "Total incorrect=", incorrect
    total_words = correct + incorrect
    percentage = 100 * float(correct)/total_words
    print "Percentage correct=", percentage

def dry_run(conn):
    correct = 0
    incorrect = 0
    
    line_num = 0
    for line in f:
        line_num += 1
        
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
                #print "---------------------------"
                #print line
                #print "My solution(s):"
                solutions = solveObject.get_all_solutions()
                #for sol in solutions:
                #    print "Solution #:"
                #    for s in sol:
                #       print "           %s %s" % (s.grapheme, s.reading)
                #print "---------------------------"
            else:
                pass
                #print line

            s = 'select * from line where line = ?'
            result = conn.execute(s, [line_num]).fetchall()
            previous = result[0]['correct']
            if previous == '1':
                print "Regression: %s " % (line)
    
        else:
            correct += 1
            s = 'select * from line where line = ?'
            result = conn.execute(s, [line_num]).fetchall()
            previous = result[0]['correct']
            if previous == '0':
                print "Regression: %s " % (line)



def make_db():
    dbpath = 'dbs/accuracy.sqlite'
    
    if os.path.exists(dbpath):
        os.remove(dbpath)
        
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON')
    
    table = '''
        CREATE TABLE line(
            line       INTEGER PRIMARY KEY,
            correct   BOOLEAN DEFAULT FALSE
        )
        '''
    c.execute(table)

if __name__ == "__main__":
    
    dbpath = 'dbs/accuracy.sqlite'
        
    #make_db()
    conn = sqlite3.connect(dbpath)
    conn.row_factory = sqlite3.Row

    #save(conn)
    dry_run(conn)

