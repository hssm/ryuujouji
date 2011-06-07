# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt
from sqlalchemy import MetaData
from sqlalchemy.sql import select, bindparam, and_, or_

import db
import tools

conn = db.get_connection()
meta = MetaData()
meta.bind = conn.engine
meta.reflect()
reading_t = meta.tables['reading']
segment_t = meta.tables['segment']
word_t = meta.tables['word']

word_s = select([word_t]).\
                where(word_t.c['keb'].like(bindparam('character')))

word_read_s = select([word_t, segment_t],\
                and_(segment_t.c['reading_id']==bindparam('reading_id'),
                     word_t.c['id']==segment_t.c['word_id']))


def words_with_char(char):
    """Returns a list of database rows (as tuples) of every word in the 
    database that contains char."""
    
    words = conn.execute(word_s, character='%'+char+'%').fetchall()
    return words

def reading_id(char, reading):
    """Returns the database id of the reading of char. Reading can be either
    hiragana or katakana (on or kun readings can be found with either)."""
    #Get both the hiragana and katakana form of reading
    if tools.is_kata(reading[0]):
        k_reading = reading
        h_reading = tools.kata_to_hira(reading)
    else:
        h_reading = reading
        k_reading = tools.hira_to_kata(reading)
        
    s = select([reading_t], and_(reading_t.c['character']==char,
                                 or_(reading_t.c['reading']==h_reading,
                               reading_t.c['reading']==k_reading)))
    result = conn.execute(s).fetchall()
    if len(result) <= 0:
        return None
    else:
        return result[0].id

def words_with_char_and_reading(char, reading, **kwargs):
    print kwargs
    r_id = reading_id(char, reading)   
    result = conn.execute(word_read_s, reading_id=r_id)
    return result
    
if __name__ == '__main__':
    #for word in words_with_char(u'新'):
    #    print word.keb, word.reb
        
    for word in words_with_char_and_reading(u'人', u'ひと', tags=(0,5,2)):
        pass #print word.keb, word.reb
    