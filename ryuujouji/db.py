import os
import time
from sqlalchemy import create_engine, Table, Column, Unicode, \
                       String, Boolean, ForeignKey, MetaData
from sqlalchemy.sql import select, and_, or_

READINGS_PATH = "../dbs/readings.sqlite"
JMDICT_PATH = "../dbs/jmdict.sqlite"
KANJIDIC_PATH = "../dbs/kanjidic.sqlite"

r_meta = MetaData()
r_engine = None

reading_t = Table('reading', r_meta,
            Column('character', Unicode, primary_key=True),
            Column('reading', Unicode, primary_key=True),
            Column('type', String, primary_key=True),
            Column('affix', String, primary_key=True),
            Column('has_okurigana', Boolean, nullable=False))

def init():
    global r_engine
    global r_meta

    if not os.path.exists(READINGS_PATH):
        if not os.path.exists(KANJIDIC_PATH):
            print "No kanjidic database found at %s" % KANJIDIC_PATH
            print "Cannot continue without it."
            return
        r_engine = create_engine('sqlite:///' + READINGS_PATH)
        r_meta.create_all(r_engine)
        db_populate_readings()
    else:
        r_engine = create_engine('sqlite:///' + READINGS_PATH)

def db_populate_readings():
    kd_engine = create_engine('sqlite:///' + KANJIDIC_PATH)
    kd_meta = MetaData()
    kd_meta.bind = kd_engine
    kd_meta.reflect()

    kd_reading = kd_meta.tables['reading']
    kd_nanori = kd_meta.tables['nanori']

    reading_l = []
    n_to_save = 500
    n = 0
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

    s = select([kd_nanori])
    nanori = kd_engine.execute(s)

    for n in nanori:
        reading_l.append({'character':n.character_literal,
                          'reading':n.nanori,
                           'type':'nanori',
                           'affix':'none',
                           'has_okurigana':False})

    r_engine.execute(reading_t.insert(), reading_l)
    print 'Filling database with kanji/reading data took '\
            '%s seconds' % (time.time() - start)

def get_readings_meta():
        engine = create_engine('sqlite:///' + READINGS_PATH)
        meta = MetaData()
        meta.bind = engine
        return meta

def get_kanjidic_meta():
        engine = create_engine('sqlite:///' + KANJIDIC_PATH)
        meta = MetaData()
        meta.bind = engine
        return meta

def get_jmdict_meta():
        engine = create_engine('sqlite:///' + JMDICT_PATH)
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