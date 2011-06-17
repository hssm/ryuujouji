# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
import time
import codecs
from sqlalchemy import create_engine, Table, Column, Unicode, UniqueConstraint,\
                       String, Integer, MetaData
from sqlalchemy.sql import select, or_

filedir = os.path.dirname(__file__)
db_path = os.path.join(filedir, 'dbs')

READINGS_PATH = os.path.join(db_path, 'readings.sqlite')
KANJIDIC_PATH = os.path.join(db_path, 'kanjidic.sqlite')
OTHER_READINGS_PATH = os.path.join(db_path, 'other_readings')


r_meta = MetaData()
r_engine = None

reading_t = Table('reading', r_meta,
                  Column('id', Integer, primary_key=True),
                  Column('character', Unicode(1), index=True),
                  Column('reading', Unicode, index=True),
                  Column('okurigana', Unicode),
                  Column('type', String),
                  UniqueConstraint('character', 'reading', 'okurigana')
                  )

def init():
    global r_engine
    global r_meta

    if not os.path.exists(READINGS_PATH):
        if not os.path.exists(KANJIDIC_PATH):
            print "No kanjidic database found at %s" % KANJIDIC_PATH
            print "Cannot continue without it."
            return
        if not os.path.exists(OTHER_READINGS_PATH):
            print "No other_readings file found at %s" % OTHER_READINGS_PATH
            print "Cannot continue without it."
            return            
            
        r_engine = create_engine('sqlite:///' + READINGS_PATH)
        r_meta.create_all(r_engine)       
        db_populate_kanji_readings()
    else:
        r_engine = create_engine('sqlite:///' + READINGS_PATH)
        
        
def db_populate_kanji_readings():
    print "Filling database with kanji/reading data..."
    kd_engine = create_engine('sqlite:///' + KANJIDIC_PATH)
    kd_meta = MetaData()
    kd_meta.bind = kd_engine
    kd_meta.reflect()
    kd_reading = kd_meta.tables['reading']
    
    reading_l = []
    start = time.time()

    s = select([kd_reading], or_(kd_reading.c['r_type'] == 'ja_on',
                                 kd_reading.c['r_type'] == 'ja_kun'))
    readings = kd_engine.execute(s)

    for r in readings:
        reading = r.reading
        if r.reading[-1] == u"-":
            reading = reading[:-1]
        elif r.reading[0] == u"-":
            reading = reading[1:]
        
        (re, s, o) = reading.partition(".")
        
        #insert the reading twice, once with the okurigana portion
        #and once without. If it already had no okurigana it is simply replaced
        reading_l.append({'character':r.character_literal,
                          'reading':re,
                          'okurigana':o,
                          'type':r.r_type})
        
        reading_l.append({'character':r.character_literal,
                  'reading':re,
                  'okurigana':u'',
                  'type':r.r_type})

    f = codecs.open(OTHER_READINGS_PATH, encoding='utf-8')
    for line in f:
        line = line.strip('\n')
        (k, s, r) = line.partition(",")
        reading_l.append({'character':k, 'reading':r, 'type':'other',
                          'okurigana':u''})
        
    r_engine.execute(reading_t.insert().prefix_with("OR REPLACE"), reading_l)

    print 'Filling database with kanji/reading data took '\
            '%s seconds' % (time.time() - start)
 

def get_connection():
        engine = create_engine('sqlite:///' + READINGS_PATH)
        return engine.connect()


if __name__ == "__main__":
    try:
        os.remove(READINGS_PATH)
    except:
        pass
    init()