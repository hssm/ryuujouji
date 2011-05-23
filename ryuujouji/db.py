# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
import time
from sqlalchemy import create_engine, Table, Column, Unicode, \
                       String, Boolean, Integer, ForeignKey, MetaData
from sqlalchemy.sql import select, and_, or_

READINGS_PATH = "../dbs/readings.sqlite"
JMDICT_PATH = "../dbs/jmdict.sqlite"
KANJIDIC_PATH = "../dbs/kanjidic.sqlite"

#readings
r_meta = MetaData()
r_engine = None


reading_t = Table('reading', r_meta,
                  Column('id', Integer, primary_key=True),
                  Column('character', Unicode, index=True),
                  Column('reading', Unicode, index=True),
                  Column('type', String),
                  Column('affix', String),
                  Column('has_okurigana', Boolean, nullable=False))

word_t = Table('word', r_meta,
               Column('id', Integer, primary_key=True),
               Column('keb', Unicode),
               Column('reb', Unicode))

solution_t = Table('solution', r_meta,
                   Column('id', Integer, primary_key=True),
                   Column('word_id', Integer, ForeignKey('word.id')))

segment_t = Table('segment', r_meta,
                   Column('id', Integer, primary_key=True),
                   Column('solution_id', Integer, ForeignKey('solution.id')),
                   Column('reading_id', Integer, ForeignKey('reading.id')),
                   Column('index', Integer))


def init():
    global r_engine
    global r_meta

    if not os.path.exists(READINGS_PATH):
        if not os.path.exists(KANJIDIC_PATH):
            print "No kanjidic database found at %s" % KANJIDIC_PATH
            print "Cannot continue without it."
            return
        if not os.path.exists(JMDICT_PATH):
            print "No jmdict database found at %s" % KANJIDIC_PATH
            print "Cannot continue without it."
            return
        r_engine = create_engine('sqlite:///' + READINGS_PATH)
        r_meta.create_all(r_engine)       
        db_populate_kanji_readings()
        db_populate_words()
    else:
        r_engine = create_engine('sqlite:///' + READINGS_PATH)
    

def db_populate_kanji_readings():
    print "Filling database with kanji/reading data..."
    kd_engine = create_engine('sqlite:///' + KANJIDIC_PATH)
    kd_meta = MetaData()
    kd_meta.bind = kd_engine
    kd_meta.reflect()

    kd_reading = kd_meta.tables['reading']
    kd_nanori = kd_meta.tables['nanori']

    reading_l = []
    start = time.time()

    s = select([kd_reading], or_(kd_reading.c['r_type'] == 'ja_on',
                                 kd_reading.c['r_type'] == 'ja_kun'))
    readings = kd_engine.execute(s)
    for r in readings:
        affix = "none"
        reading = r.reading
        if r.reading[-1] == "-":
            affix = "prefix"
            reading = reading[:-1]
        elif r.reading[0] == "-":
            affix = "suffix"
            reading = reading[1:]

        has_oku = False
        if "." in r.reading:
            has_oku = True

        reading_l.append({'character':r.character_literal,
                          'reading':reading,
                          'type':r.r_type,
                          'affix':affix,
                          'has_okurigana':has_oku})

#    s = select([kd_nanori])
#    nanori = kd_engine.execute(s)
#
#    for n in nanori:
#        reading_l.append({'character':n.character_literal,
#                          'reading':n.nanori,
#                           'type':'nanori',
#                           'affix':'none',
#                           'has_okurigana':False})

    r_engine.execute(reading_t.insert(), reading_l)

    print 'Filling database with kanji/reading data took '\
            '%s seconds' % (time.time() - start)


def db_populate_words():
    print "Filling database with word/reading data..."
    jd_engine = create_engine('sqlite:///' + JMDICT_PATH)
    jd_meta = MetaData()
    jd_meta.bind = jd_engine
    jd_meta.reflect()

    k_ele = jd_meta.tables['k_ele']
    r_ele = jd_meta.tables['r_ele']

    word_l = []
    start = time.time()

    s = select([k_ele, r_ele],
                k_ele.c['entry_ent_seq'] == r_ele.c['entry_ent_seq'])
    words = jd_engine.execute(s)
    
    for word in words:
        word_l.append({'keb':word.keb, 'reb':word.reb})
    
    r_engine.execute(word_t.insert(), word_l)
    print 'Filling database with word/reading data took '\
            '%s seconds' % (time.time() - start)

def get_meta():
        engine = create_engine('sqlite:///' + READINGS_PATH)
        meta = MetaData()
        meta.bind = engine
        return meta


if __name__ == "__main__":
    if True:
        try:
            os.remove(READINGS_PATH)
        except:
            pass
    init()