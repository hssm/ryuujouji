# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import sqlite3
import time
import os

from word import Word
JMDICT_PATH = os.path.join('dbs/jmdict.sqlite')

conn = None

def make_connection(db_path):
    global conn    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

def populate_db():
    print "Filling database with word/reading data from JMdict..."
    
    if not os.path.exists(JMDICT_PATH):
        print "No jmdict database found at %s" % JMDICT_PATH
        print "Cannot continue without it."
        return
        
    #get connection to jmdict database 
    jm_conn = sqlite3.connect(JMDICT_PATH)
    jm_conn.row_factory = sqlite3.Row

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

    results = jm_conn.execute(s)
    
    for r in results:
        #some words have no kanji elements
        if r['k_ele_keb'] is None:
            continue
        #if this entry has a restricted reb, only apply it to the
        #corresponding keb
        if r['re_restr_keb'] is not None:
            if r['re_restr_keb'] == r['k_ele_keb']:
                #print r['k_ele_keb'], r['r_ele_reb']
                word = Word(conn, r['k_ele_keb'], r['r_ele_reb'])
                word.save()
        else: #otherwise, all rebs apply to all kebs in this entry
            #but some readings don't use kanji, so no related kebs
            if r['r_ele_re_nokanji'] is not None:
                #print r['k_ele_keb'], r['r_ele_reb']
                word = Word(conn, r['k_ele_keb'], r['r_ele_reb'])
                word.save()
    conn.commit()
    print 'Filling database with word/reading data took '\
            '%s seconds' % (time.time() - start)


def dry_run():
    """Don't save any changes to the database, but check if the present
     parsing behaviour breaks the solving of an already-solved entry.
     """

    start = time.time()
    results = conn.execute('select word, reading, solved from word').fetchall()

    newly_solved = 0
    regressed = 0
    for row in results:
        word = Word(conn, row['word'], row['reading'])

        if row['solved'] is 1:
            if word.segments is None:
                regressed += 1
                print "Regression for word %s == %s" % (row['word'], row['reading'])
        else:
            if word.segments is not None:
                newly_solved += 1
                print "New word found %s == %s" % (row['word'], row['reading'])
    print "The changes will solve %s entries. " % newly_solved
    print "The changes will unsolve %s entries. " % regressed
    print 'took %s seconds' % (time.time() - start)


def print_solving_stats():
    words = conn.execute('select count() from word').fetchone()
    n = words[0]
    
    s = "select count() from word where solved=1" 
    found = conn.execute(s).fetchone()
    nf = found[0]
    if n != 0:
        percent = float(nf) / float(n) * 100
    else:
        percent = 0
    print "There are %s entries in the database. A solution has been found"\
    " for %s of them. (%f%%)" % (n, nf, percent)   


if __name__ == "__main__":
    dbpath = 'dbs/jmdict_solutions.sqlite'
    
    from word_db import create_db
    create_db(dbpath)
    make_connection(dbpath)
    populate_db()
     
    print_solving_stats()     
#    dry_run()

#There are 159207 entries in the database. A solution has been found for 148395 of them. (93.208841%)
#There are 159207 entries in the database. A solution has been found for 148388 of them. (93%)
