# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
import time
import codecs
import sqlite3
from paths import READINGS_PATH, KANJIDIC_PATH, OTHER_READINGS_PATH

conn = None

create_table =\
'''
CREATE TABLE reading(
    id        INTEGER PRIMARY KEY,
    character TEXT,
    reading   TEXT,
    okurigana TEXT,
    type      TEXT,
    UNIQUE(character, reading, okurigana) ON CONFLICT REPLACE)
'''

def init():
    global conn

    if not os.path.exists(READINGS_PATH):
        if not os.path.exists(KANJIDIC_PATH):
            print "No kanjidic database found at %s" % KANJIDIC_PATH
            print "Cannot continue without it."
            return
        if not os.path.exists(OTHER_READINGS_PATH):
            print "No other_readings file found at %s" % OTHER_READINGS_PATH
            print "Cannot continue without it."
            return            
            
        conn = sqlite3.connect(READINGS_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(create_table)
        c.execute('CREATE INDEX character_idx ON reading(character)')
        c.execute('CREATE INDEX reading_idx ON reading(reading)')
        db_populate_kanji_readings()
    else:
        conn = sqlite3.connect(READINGS_PATH)
        conn.row_factory = sqlite3.Row
        
        
def db_populate_kanji_readings():
    print "Filling database with kanji/reading data..."
    c = conn.cursor()
    
    kd_conn = sqlite3.connect(KANJIDIC_PATH)
    kd_conn.row_factory = sqlite3.Row
    kd_c = kd_conn.cursor()
    
    reading_l = []
    start = time.time()

    s = "SELECT * FROM reading WHERE r_type='ja_on' OR r_type='ja_kun'"
    readings = kd_c.execute(s).fetchall()

    for r in readings:
        reading = r['reading']
        if reading[-1] == u"-":
            reading = reading[:-1]
        elif reading[0] == u"-":
            reading = reading[1:]
        
        (re, s, o) = reading.partition(".")
        
        #insert the reading twice, once with the okurigana portion
        #and once without. If it already had no okurigana it is simply replaced
        reading_l.append([r['character_literal'], re, o, r['r_type']])
        reading_l.append([r['character_literal'], re, u'', r['r_type']])

    f = codecs.open(OTHER_READINGS_PATH, encoding='utf-8')
    for line in f:
        line = line.strip('\n')
        (k, s, r) = line.partition(",")
        reading_l.append([k, r, u'', 'other'])
        
    c.executemany('''INSERT INTO reading(character, reading, okurigana, type)
                     VALUES (?,?,?,?)''', reading_l)

    print 'Filling database with kanji/reading data took '\
            '%s seconds' % (time.time() - start)
    conn.commit()
 

def get_connection():
        conn = sqlite3.connect(READINGS_PATH)
        return conn


if __name__ == "__main__":
    try:
        os.remove(READINGS_PATH)
    except:
        pass
    init()