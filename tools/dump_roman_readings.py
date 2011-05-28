# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import select, and_
 
JMDICT_PATH = "../dbs/jmdict.sqlite"

def dump_roman_readings():
    print "Dumping roman character reading data..."
    engine = create_engine('sqlite:///' + JMDICT_PATH)
    meta = MetaData()
    meta.bind = engine
    meta.reflect()

    k_ele = meta.tables['k_ele']
    r_ele = meta.tables['r_ele']

    s = select([k_ele.c['keb'], k_ele.c['entry_ent_seq']])
    kebs = engine.execute(s)
    
    f = open('roman_readings', 'w')
    romans = []
    for k in kebs:
        if len(k.keb) == 1 and k.keb >= u'\uFF21' and k.keb <= u'\uFF5A':
            s = select([r_ele.c['reb']],
                        r_ele.c.entry_ent_seq==k.entry_ent_seq)
            
            rebs = engine.execute(s)
            for r in rebs:
                #print k.keb, r.reb
                romans.append(k.keb + ',' + r.reb)
    romans.extend(get_manual_additions())
    romans.sort()
    for r in romans:
        f.write(r + '\n')

    print "Done."

def get_manual_additions():
    """Some entries that seem to be missing from JMdict."""
    
    #These are wide latin characters.
    extra = ['ｍ,エム', 'ｓ,エス']
    return extra

if __name__ == "__main__":
    if not os.path.exists(JMDICT_PATH):
        print "No jmdict database found at %s" % JMDICT_PATH
        print "Cannot continue without it."
    else:
        dump_roman_readings()

        #no lower case m, no lower case s