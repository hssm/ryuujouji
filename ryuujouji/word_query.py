# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

from sqlalchemy.sql import select, bindparam, and_, func


from solver import solve_reading
from segments import SegmentTag
import word_db
import reading_query
from word_db import SolveTag, word_t, segment_t, tag_t

select_word_with_char = select([word_t]).\
                where(word_t.c['word'].like(bindparam('character')))

select_word_with_char_and_reading = select([word_t, segment_t],\
                     and_(segment_t.c['reading_id']==bindparam('reading_id'),
                          word_t.c['id']==segment_t.c['word_id']))

select_unsolved_words = select([word_t], word_t.c['solved']==SolveTag.Unchecked)

   
        
class WordQuery():
    
    def __init__(self, words_db_path):
        self.w_conn = word_db.get_connection(words_db_path)
        
    def add_words(self, word_list, solve=True):
        """Adds the given words and their readings to the database. The word_list
        argument should be a list of dictionaries of the form
        {'word':word, 'reading':reading}."""
        self.w_conn.execute(word_t.insert().prefix_with('OR IGNORE'), word_list)
        
        #After we save the words to the database, we populate it with the 
        #segments of those words.
        if solve == True:
            self.solve_new()

    def get_segments(self, word, reading):
        s = select([segment_t],
from_obj=[segment_t.join(word_t, and_(word_t.c['word']==word,
                                      word_t.c['reading']==reading, 
                                      segment_t.c['word_id']==word_t.c['id'])
                         )
          ])
                   
        segments = self.w_conn.execute(s).fetchall()
        return segments
                   

    def get_segment_tags(self, seg_id):
        s = select([tag_t],
from_obj=[tag_t.join(segment_t, and_(segment_t.c['id']==seg_id,
                                     segment_t.c['id']==tag_t.c['segment_id']))])
        tags = self.w_conn.execute(s).fetchall()
        return tags
       
    def save_solved(self, solved_l, segment_l, tag_l):
        u = word_t.update().where(word_t.c['id']==
                                  bindparam('word_id')).\
                                  values(solved=bindparam('solved'))
    
        #Length checks are there because, for some reason, it seems to add
        #an empty row if the list is just []
        if len(solved_l) > 0:
            self.w_conn.execute(u, solved_l)
        if len(segment_l) > 0:
            self.w_conn.execute(segment_t.insert(), segment_l)
        if len(tag_l) > 0:
            self.w_conn.execute(tag_t.insert(), tag_l)
            

    def solve_new(self):
        
        #Find the next segment ID
        count = self.w_conn.execute(func.count(segment_t.c['id'])).fetchall()
        seg_id = count[0][0] #first item of first row is the count
        new_words = self.w_conn.execute(select_unsolved_words).fetchall()
        save_now = 0

        solved_l = []    
        segment_l = []
        tag_l = []
        
        for word in new_words:
            segments = solve_reading(word.word, word.reading)
            if len(segments) == 0:
                solved_l.append({'word_id':word.id, 'solved':SolveTag.Unsolvable})
            else:
                for seg in segments:
                    seg_id += 1
                    solved_l.append({'word_id':word.id, 'solved':SolveTag.Solved})
                    segment_l.append({'id':seg_id,
                                      'word_id':word.id,
                                      'reading_id':seg.reading_id,
                                      'is_kanji':seg.is_kanji,
                                      'index':seg.nth_kanji,
                                      'indexr':seg.nth_kanjir})
                    for tag in seg.tags:
                        tag_l.append({'segment_id':seg_id,
                                           'tag':tag})
            save_now += 1
            if save_now > 20000:
                save_now = 0
                self.save_solved(solved_l, segment_l, tag_l)
                solved_l = []
                segment_l = []
                tag_l = []
        self.save_solved(solved_l, segment_l, tag_l)
    
    #TODO
    def remove_word(self, word, reading):
        """Remove a word/reading pair from the database."""
        pass
    
    def clear_words(self):
        """Remove all existing words from the database. Solved segments of those
        words will also be deleted."""
    
        self.w_conn.execute(word_t.delete())
        self.clear_segments()
    
    def clear_segments(self):
        """Remove all solved segments from the database."""
    
        self.w_conn.execute(segment_t.delete())
        self.w_conn.execute(tag_t.delete())

    def contains_char(self, char, **kwargs):
        """Returns a list of database rows (as tuples) of every word in the 
        solutions database that contains char."""
    
        count = kwargs.get('count', 1)
            
        in_keb = '%%'
        if count > 0:
            for n in range(0, count):
                in_keb += '%s%%' % char
            words = self.w_conn.execute(select_word_with_char, character=in_keb).fetchall()
            return words
        return []
    
    def words_by_reading(self, char, reading, **kwargs):
        """Returns a list of database rows (as tuples) of every word in the 
        solutions database that contains char with reading."""
              
        r_id = reading_query.get_id(char, reading)
        return self.words_by_reading_id(r_id, **kwargs)

    def words_by_reading_id(self, reading_id, **kwargs):
        """Returns a list of database rows (as tuples) of every word in the 
        solutions database that contains reading_id."""
        
        tags = kwargs.get('tags', ())
        index = kwargs.get('index', None)
        
        r_id = reading_id
        query = select_word_with_char_and_reading
    
        if len(tags) > 0:
            query = query.\
            select_from(segment_t.join\
                        (tag_t, and_(tag_t.c['segment_id']==segment_t.c['id'],
                                       tag_t.c['tag'].in_(tags))))    
        
        if index is not None:
            if index < 0:
                rindex = (index*-1)-1
                query = query.where(segment_t.c['indexr']==rindex)
            else:
                query = query.where(segment_t.c['index']==index)
        
        result = self.w_conn.execute(query, reading_id=r_id).fetchall()
        return result

    def print_solving_stats(self):
        s = select([word_t])
        words = self.w_conn.execute(s).fetchall()
        n = len(words)
        
        s = select([word_t], word_t.c['solved'] == SolveTag.Solved)
        found = self.w_conn.execute(s).fetchall()
        nf = len(found)
        if n != 0:
            percent = float(nf) / float(n) * 100
        else:
            percent = 0
        print "There are %s entries in the database. A solution has been found"\
        " for %s of them. (%d%%)" % (n, nf, percent)    
    
if __name__ == '__main__':
    #dbpath = 'dbs/test_query.sqlite'
    dbpath = 'dbs/jmdict_solutions.sqlite'
    #word_db.create_db(dbpath)
    q = WordQuery(dbpath)
#    for word in q.contains_char(u'漢'):
#        print word.word, word.reading
    tags = [SegmentTag.Dakuten, SegmentTag.Handakuten]
    #results = q.words_by_reading(u'漢', u'かん')
    
#    q.clear_words()
#    q.add_words([{'word':u'建て替える', 'reading':u'たてかえる'},
#               {'word':u'漢字', 'reading':u'かんじ'},
#               {'word':u'漢字時代', 'reading':u'かんじじだい'},
#               {'word':u'漢字時代', 'reading':u'かんじじだいおおお'},
#               {'word':u'半分', 'reading':u'はんぶん'},
#               {'word':u'一つ', 'reading':u'ひとつ'}])
    
    results = q.words_by_reading(u'人', u'ひと', tags=tags, index=2)
    
    for word in results:
        print word.word, word.reading