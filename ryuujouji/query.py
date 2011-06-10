# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt
from sqlalchemy import MetaData
from sqlalchemy.sql import select, bindparam, and_, or_

import db
import tools
from segments import SegmentTag

conn = db.get_connection()
meta = MetaData()
meta.bind = conn.engine
meta.reflect()
reading_t = meta.tables['reading']
segment_t = meta.tables['segment']
word_t = meta.tables['word']
tag_t = meta.tables['tag']

word_s = select([word_t]).\
                where(word_t.c['keb'].like(bindparam('character')))

word_read_s = select([word_t, segment_t],\
                and_(segment_t.c['reading_id']==bindparam('reading_id'),
                     word_t.c['id']==segment_t.c['word_id']))


def reading_id(char, reading):
    """Returns the database id of the reading of char. Reading can be either
    hiragana or katakana (on or kun readings can be found with either)."""
    
    if len(reading) == 0:
        return None
    
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

def contains_char(char, **kwargs):
    """Returns a list of database rows (as tuples) of every word in the 
    database that contains char."""

    count = kwargs.get('count', 1)
        
    in_keb = '%%'
    if count > 0:
        for n in range(0, count):
            in_keb += '%s%%' % char
        words = conn.execute(word_s, character=in_keb).fetchall()
        return words
    return []

def contains_char_reading(char, reading, **kwargs):
    """Returns a list of database rows (as tuples) of every word in the 
    database that contains char with reading."""
    
    tags = kwargs.get('tags', ())
    index = kwargs.get('index', None)
    
    r_id = reading_id(char, reading)
    query = word_read_s

    if len(tags) > 0:
        query = query.\
        select_from(segment_t.join(tag_t,
                                   and_(tag_t.c['segment_id']==segment_t.c['id'],
                                   tag_t.c['tag'].in_(tags))))    
    
    if index is not None:
        if index < 0:
            rindex = (index*-1)-1
            query = query.where(segment_t.c['nth_kanjir']==rindex)
        else:
            query = query.where(segment_t.c['nth_kanji']==index)
      
    result = conn.execute(query, reading_id=r_id).fetchall()
    return result
    
if __name__ == '__main__':
#    for word in contains_char(u'人', count=2):
#        print word.keb, word.reb
    tags = [SegmentTag.Dakuten, SegmentTag.Handakuten]
    results = contains_char_reading(u'人', u'じん')
    for word in results:
        print word.keb, word.reb
    print "Found %s" % len(results)