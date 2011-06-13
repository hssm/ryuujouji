# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import time
import os

from sqlalchemy import MetaData, create_engine
from sqlalchemy.sql import select


import solutions_db
import query
from query import get_readings

JMDICT_PATH = os.path.join('dbs/jmdict.sqlite')

conn = solutions_db.get_connection()
meta = MetaData()
meta.bind = conn.engine
meta.reflect()

word_t = meta.tables['word']
segment_t = meta.tables['segment']
tag_t = meta.tables['tag']

def populate_db():
    print "Filling database with word/reading data from JMdict..."
    
    if not os.path.exists(JMDICT_PATH):
        print "No jmdict database found at %s" % JMDICT_PATH
        print "Cannot continue without it."
        return
        
    jd_engine = create_engine('sqlite:///' + JMDICT_PATH)
    jd_meta = MetaData()
    jd_meta.bind = jd_engine
    jd_meta.reflect()

    k_ele = jd_meta.tables['k_ele']
    r_ele = jd_meta.tables['r_ele']
    re_restr = jd_meta.tables['re_restr']

    word_l = []
    start = time.time()
 
    s = select([r_ele, re_restr.c['keb'], k_ele.c['keb']], from_obj=[
            r_ele.outerjoin(re_restr, re_restr.c['r_ele_id'] == r_ele.c['id']).\
            outerjoin(k_ele, k_ele.c['entry_ent_seq'] == r_ele.c['entry_ent_seq'])
            ], use_labels=True)
 
    results = jd_engine.execute(s)
    
    for r in results:
        #some words have no kanji elements
        if r.k_ele_keb is None:
            continue
        #if this entry has a restricted reb, only apply it to the
        #corresponding keb
        if r.re_restr_keb is not None:
            if r.re_restr_keb == r.k_ele_keb:
                word_l.append({'word':r.k_ele_keb, 'reading':r.r_ele_reb})
        else: #otherwise, all rebs apply to all kebs in this entry
            #but some readings don't use kanji, so no related kebs
            if r.r_ele_re_nokanji is not None:
                word_l.append({'word':r.k_ele_keb, 'reading':r.r_ele_reb})

    query.add_words(word_l, solve=False)
    print 'Filling database with word/reading data took '\
            '%s seconds' % (time.time() - start)


def fill_solutions():
    print 'Solving segments...(takes about 220 seconds)'
    query.clear_segments()
    
    start = time.time()
    query.fill_segments()
    print 'took %s seconds' % (time.time() - start)


def dry_run():
    """Don't save any changes to the database, but check if the present
     parsing behaviour breaks the solving of an already-solved entry.
     """
     
    start = time.time()
    s = select([word_t])
    words = conn.execute(s)
    newly_solved = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        if word.found == True:
            if len(segments) == 0:
                print "Regression for word %s == %s" %(word.keb, word.reb)
        else:
            if len(segments) > 0:
                newly_solved += 1
                print "New found word %s" % word.keb, word.reb
    print "The changes will solve another %s entries. " % newly_solved


def print_stats():
    s = select([word_t])
    words = conn.execute(s).fetchall()
    n = len(words)
    
    s = select([word_t], word_t.c['found'] == True)
    found = conn.execute(s).fetchall()
    nf = len(found)
    
    percent = float(nf) / float(n) * 100
    print "There are %s entries in JMdict. A solution has been found for %s"\
          " of them. (%d%%)" % (n, nf, percent)


if __name__ == "__main__":
    solutions_db.set_solutions_path('dbs/testjmdict.sqlite')
    query.
    populate_db()
#   fill_solutions() 
#    print_stats()     
#    dry_run()

#There are 159207 entries in JMdict. A solution has been found for 131447 of them. (82%)

