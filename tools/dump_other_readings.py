# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import select, and_
 
JMDICT_PATH = "../ryuujouji/dbs/jmdict.sqlite"

def dump_other_readings():
    print "Dumping extra character reading data..."
    engine = create_engine('sqlite:///' + JMDICT_PATH)
    meta = MetaData()
    meta.bind = engine
    meta.reflect()

    k_ele = meta.tables['k_ele']
    r_ele = meta.tables['r_ele']

    s = select([k_ele.c['keb'], k_ele.c['entry_ent_seq']])
    kebs = engine.execute(s)
    
    f = open('other_readings', 'w')
    others = []
    for k in kebs:
        if len(k.keb) == 1:
            s = select([r_ele.c['reb']],
                        r_ele.c.entry_ent_seq==k.entry_ent_seq)

            rebs = engine.execute(s)
            for r in rebs:
                others.append(k.keb + ',' + r.reb)
            
    others.extend(get_manual_additions())
    others.sort()
    for r in others:
        f.write(r + '\n')

    print "Done."

def get_manual_additions():
    """Some entries that seem to be missing from JMdict, or just
    useful additions."""
    
    #These are wide latin characters.
    extra = [u'ｍ,エム', u'ｓ,エス', u'Ｎ,エン', u'ｎ,エン']
    return extra

if __name__ == "__main__":
    if not os.path.exists(JMDICT_PATH):
        print "No jmdict database found at %s" % JMDICT_PATH
        print "Cannot continue without it."
    else:
        dump_other_readings()