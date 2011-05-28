# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import select, or_
 
KANJIDIC_PATH = "../dbs/kanjidic.sqlite"

def dump_readings():
    print "Dumping kanji/reading data..."
    engine = create_engine('sqlite:///' + KANJIDIC_PATH)
    meta = MetaData()
    meta.bind = engine
    meta.reflect()

    reading = meta.tables['reading']

    s = select([reading], or_(reading.c['r_type'] == 'ja_on',
                                 reading.c['r_type'] == 'ja_kun'))
    readings = engine.execute(s)
    f = open('kanji_readings', 'w')
    for r in readings:
        f.write(r.character_literal + ',' +r.reading + '\n')

    print "Done."
            
            
            
if __name__ == "__main__":
    if not os.path.exists(KANJIDIC_PATH):
        print "No kanjidic database found at %s" % KANJIDIC_PATH
        print "Cannot continue without it."
    else:
        dump_readings()