# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

from sqlalchemy.sql import select, bindparam, and_, or_, func

import readings_db
import words_db
import tools
from reading import solve_reading
from segments import SegmentTag

r_conn = readings_db.get_connection()
reading_t = readings_db.reading_t

s_conn = None
segment_t = None
word_t = None
tag_t = None
word_s = None
word_read_s = None
segment_s = None

class DatabaseNotSetException(Exception): pass
can_query = False

def set_words_db_path(path):
    words_db.words_path = path

def init():
    global s_conn, segment_t, word_t, tag_t
    if words_db.words_path is None:
        can_query = False
        raise DatabaseNotSetException("Word database has not been set.")
    else:
        s_conn = words_db.get_connection()
        segment_t = words_db.segment_t
        word_t = words_db.word_t
        tag_t = words_db.tag_t
        create_queries()
        can_query = True

def create_queries():
    global word_s, word_read_s, segment_s
    word_s = select([word_t]).\
                    where(word_t.c['word'].like(bindparam('character')))
    
    word_read_s = select([word_t, segment_t],\
                    and_(segment_t.c['reading_id']==bindparam('reading_id'),
                         word_t.c['id']==segment_t.c['word_id']))    
    
    segment_s = select([word_t], word_t.c['found']==False)

def start_querying():
    if not can_query:
        init()

def get_readings(word, reading):
    return solve_reading(word, reading)

found_l = []
segment_l = []
tag_l = []

def save_found():
    global found_l, segment_l, tag_l
    start_querying()
    
    u = word_t.update().where(word_t.c['id']==
                              bindparam('word_id')).\
                              values(found=bindparam('found'))

    #Length checks are there because, for some reason, it seems to add
    #an empty row if the list is just []
    if len(found_l) > 0:
        s_conn.execute(u, found_l)
    if len(segment_l) > 0:
        s_conn.execute(segment_t.insert(), segment_l)
    if len(tag_l) > 0:
        s_conn.execute(tag_t.insert(), tag_l)
        
    found_l = []    
    segment_l = []
    tag_l = []


def add_words(word_list, solve=True):
    """Adds the given words and their readings to the database. The word_list
    argument should be a list of dictionaries of the form
    {'word':word, 'reading':reading}."""
    
    start_querying()
    s_conn.execute(word_t.insert().prefix_with('OR IGNORE'), word_list)

    #After we save the words to the database, we populate it with the 
    #segments of those words.
    if solve == True:
        fill_segments()


def fill_segments():
    start_querying()
    
    #Find the next segment ID
    count = s_conn.execute(func.count(segment_t.c['id'])).fetchall()
    seg_id = count[0][0] #first item of first row is the count
    new_words = s_conn.execute(segment_s).fetchall()
    save_now = 0

    for word in new_words:
        segments = get_readings(word.word, word.reading)
        if len(segments) == 0:
            #'found' will be set to null. 'found' = null means we've already
            #tried to solve it but found no solutions
            found_l.append({'word_id':word.id})
        else:
            for seg in segments:
                seg_id += 1
    
                found_l.append({'word_id':word.id, 'found':True})
                segment_l.append({'id':seg_id,
                                  'word_id':word.id,
                                  'reading_id':seg.reading_id,
                                  'index':seg.nth_kanji,
                                  'indexr':seg.nth_kanjir})
                for tag in seg.tags:
                    tag_l.append({'segment_id':seg_id,
                                  'tag':tag})
        save_now += 1
        if save_now > 20000:
            save_now = 0
            save_found()
    save_found()
    
#TODO
def remove_word(word, reading):
    """Remove a word/reading pair from the database."""
    pass

def clear_words():
    """Remove all existing words from the database. Solved segments of those
    words will also be deleted."""
    start_querying()
    s_conn.execute(word_t.delete())
    clear_segments()

def clear_segments():
    """Remove all solved segments from the database."""
    start_querying()
    s_conn.execute(segment_t.delete())
    s_conn.execute(tag_t.delete())


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
    result = r_conn.execute(s).fetchall()
    if len(result) <= 0:
        return None
    else:
        return result[0].id

def contains_char(char, **kwargs):
    """Returns a list of database rows (as tuples) of every word in the 
    solutions database that contains char."""

    start_querying()
    count = kwargs.get('count', 1)
        
    in_keb = '%%'
    if count > 0:
        for n in range(0, count):
            in_keb += '%s%%' % char
        words = s_conn.execute(word_s, character=in_keb).fetchall()
        return words
    return []

def contains_char_reading(char, reading, **kwargs):
    """Returns a list of database rows (as tuples) of every word in the 
    solutions database that contains char with reading."""
    
    start_querying()
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
            query = query.where(segment_t.c['indexr']==rindex)
        else:
            query = query.where(segment_t.c['index']==index)
      
    result = s_conn.execute(query, reading_id=r_id).fetchall()
    return result
    
if __name__ == '__main__':
    set_words_db_path('dbs/testjmdict.sqlite')
#    for word in contains_char(u'人', count=2):
#        print word.keb, word.reb
    tags = [SegmentTag.Dakuten, SegmentTag.Handakuten]
    results = contains_char_reading(u'立', u'た')
#    for word in results:
#        print word.keb, word.reb
#    print "Found %s" % len(results)
    
    #clear_words()
    add_words([{'word':u'建て替える', 'reading':u'たてかえる'},
               {'word':u'漢字', 'reading':u'かんじ'},
               {'word':u'漢字時代', 'reading':u'かんじじだいい'},
               {'word':u'半分', 'reading':u'はんぶん'},
               {'word':u'一つ', 'reading':u'ひとつ'}])