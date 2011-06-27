# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import sqlite3
import time
import os
from word_query import WordQuery
from word_db import SolveTag
from solver import solve_reading
JMDICT_PATH = os.path.join('dbs/jmdict.sqlite')
wq = None 

def populate_db():
    print "Filling database with word/reading data from JMdict..."
    
    if not os.path.exists(JMDICT_PATH):
        print "No jmdict database found at %s" % JMDICT_PATH
        print "Cannot continue without it."
        return
    
    conn = sqlite3.connect(JMDICT_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    word_l = []
    start = time.time()

    s = '''
        SELECT  r_ele.reb AS r_ele_reb,
                r_ele.re_nokanji AS r_ele_re_nokanji,
                re_restr.keb AS re_restr_keb,
                k_ele.keb AS k_ele_keb 
        FROM r_ele
        LEFT OUTER JOIN re_restr
        ON re_restr.r_ele_id=r_ele.id
        LEFT OUTER JOIN k_ele
        ON k_ele.entry_ent_seq=r_ele.entry_ent_seq
        '''

    results = c.execute(s)

    for r in results:
        #some words have no kanji elements
        if r['k_ele_keb'] is None:
            continue
        #if this entry has a restricted reb, only apply it to the
        #corresponding keb
        if r['re_restr_keb'] is not None:
            if r['re_restr_keb'] == r['k_ele_keb']:
                word_l.append([r['k_ele_keb'], r['r_ele_reb']])
        else: #otherwise, all rebs apply to all kebs in this entry
            #but some readings don't use kanji, so no related kebs
            if r['r_ele_re_nokanji'] is not None:
                word_l.append([r['k_ele_keb'], r['r_ele_reb']])

    wq.add_words(word_l, solve=False)
    print 'Filling database with word/reading data took '\
            '%s seconds' % (time.time() - start)


def fill_solutions():
    print 'Solving segments...(takes about 70 seconds)'
    wq.clear_segments()
    start = time.time()
    wq.solve_new(unsolved=True)
    print 'took %s seconds' % (time.time() - start)


def dry_run():
    """Don't save any changes to the database, but check if the present
     parsing behaviour breaks the solving of an already-solved entry.
     """
     
    start = time.time()
    words = wq.contains_char(u'%')

    newly_solved = 0
    for word in words:
        segments = solve_reading(word.word, word.reading)
        if word.solved == SolveTag.Solved:
            if len(segments) == 0:
                print "Regression for word %s == %s" %(word.word, word.reading)
        else:
            if len(segments) > 0:
                newly_solved += 1
                #print "New found word ", word.word, word.reading
    print "The changes will solve another %s entries. " % newly_solved
    print 'took %s seconds' % (time.time() - start)


def print_stats():
    wq.print_solving_stats()


if __name__ == "__main__":
    dbpath = 'dbs/jmdict_solutions.sqlite'
    from word_db import create_db
    create_db(dbpath)
    wq = WordQuery(dbpath)
    
    populate_db()
   
    fill_solutions() 
    print_stats()     
#    dry_run()

#There are 159207 entries in the database. A solution has been found for 139520 of them. (87%)
#There are 159207 entries in JMdict. A solution has been found for 131447 of them. (82%)

