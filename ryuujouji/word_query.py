# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

from solver import solve_reading
from segments import SegmentTag
import word_db
import reading_query

from word_db import SolveTag

word_t = None
segment_t = None
tag_t =  None

       
class WordQuery():
    
    def __init__(self, words_db_path):
        self.w_conn = word_db.get_connection(words_db_path)
        
    def add_words(self, word_list, solve=True):
        """Adds the given words and their readings to the database. The word_list
        argument should be a list of dictionaries of the form
        {'word':word, 'reading':reading}."""

        self.w_conn.executemany('insert into word(word, reading) values(?,?)',
                                word_list)
        
        #After we save the words to the database, we populate it with the 
        #segments of those words.
        if solve == True:
            self.solve_new()
        
        self.w_conn.commit()

    def get_word(self, word, reading):
        """Returns the database row (as a tuple) for word with reading. If the
        word/reading combination doesn't exist, returns None."""
        
        s = 'select * from word where word=? and reading=?'
        word = self.w_conn.execute(s, [word, reading]).fetchone()
        return word
        

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
        query = '''select * from word
                    join segment
                    on word.id=segment.word_id and segment.reading_id=?
                '''
       
        if len(tags) > 0:
            tag_string = ["'"+tag+"'," for tag in tags]
            tag_string = "".join(tag_string)[:-1]

            
            query += '''join tag
                        on tag.segment_id=segment.id and tag.tag in(%s)
                     ''' % tag_string
            print query
        
        if index is not None:
            if index < 0:
                rindex = (index*-1)-1
                query = query.where(segment_t.c['indexr']==rindex)
            else:
                query = query.where(segment_t.c['index']==index)
        
        result = self.w_conn.execute(query, [r_id]).fetchall()
        return result

    def segments_by_reading(self, word, reading):
        word = self.get_word(word, reading)
        if word is None:
            return None
        return self.segments_by_word_id(word.id)
         
    def segments_by_word_id(self, word_id):
        s = 'select * from segment where segment.word_id=?'
        segments = self.w_conn.execute(s, [word_id]).fetchall()
        return segments
    

    def tags_by_segment_id(self, seg_id):
        s = '''select * from tag
               join segment
               on segment.id=? and segment.id=tag.id
            '''
        tags = self.w_conn.execute(s, [seg_id]).fetchall()
        return tags
       
    def save_solved(self, solved_l, segment_l, tag_l):      
        wor_upd = 'update word set solved=? where id=?'
        seg_upd = '''insert into segment(id, word_id, reading_id, is_kanji,
         'index', indexr) values(?,?,?,?,?,?)'''
        tag_upd = 'insert into tag(segment_id, tag) values(?,?)'
    
        #Length checks are there because, for some reason, it seems to add
        #an empty row if the list is just []
        if len(solved_l) > 0:
            self.w_conn.executemany(wor_upd, solved_l)
        if len(segment_l) > 0:
            self.w_conn.executemany(seg_upd, segment_l)
        if len(tag_l) > 0:
            self.w_conn.executemany(tag_upd, tag_l)
        self.w_conn.commit()
            

    def solve_new(self, unsolved=False):
        #Find the next segment ID
        count = self.w_conn.execute('select count() from segment').fetchall()
        seg_id = count[0][0] #first item of first row is the count
        if not unsolved:
            query = "select * from word where solved='%s'" % SolveTag.Unchecked

        else:
            query = "select * from word where solved='%s' or solved='%s'" % (
                    SolveTag.Unchecked, SolveTag.Unsolvable)

        new_words = self.w_conn.execute(query).fetchall()
        save_now = 0

        solved_l = []    
        segment_l = []
        tag_l = []
        
        for word in new_words:
            segments = solve_reading(word['word'], word['reading'])
            if len(segments) == 0:
                solved_l.append([SolveTag.Unsolvable, word['id']])
            else:
                for seg in segments:
                    seg_id += 1
                    solved_l.append([SolveTag.Solved, word['id']])
                    segment_l.append([seg_id, word['id'], seg.reading_id,
                                      seg.is_kanji, seg.index, seg.indexr])
                    for tag in seg.tags:
                        tag_l.append([seg_id, tag])
            save_now += 1
            if save_now > 2000:
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
    
        self.w_conn.execute('delete from segment')
        self.w_conn.execute('delete from tag')

    def contains_char(self, char, **kwargs):
        """Returns a list of database rows (as tuples) of every word in the 
        solutions database that contains char."""
    
        count = kwargs.get('count', 1)

        in_keb = '%%'
        if count > 0:
            for n in range(0, count):
                in_keb += '%s%%' % char
            s = 'select * from word where word.word like ?' 
            
            words = self.w_conn.execute(s, [in_keb]).fetchall()
            return words
        return []
    

    def print_solving_stats(self):
        words = self.w_conn.execute('select count() from word').fetchall()
        n = words[0][0]
        
        s = "select count() from word where solved='%s'" % SolveTag.Solved 
        found = self.w_conn.execute(s).fetchall()
        nf = found[0][0]
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
#    results = q.contains_char(u'人', count=2)
#    for word in results:
#        print word['word'], word['reading']
#    print 'found', len(results)

    #results = q.words_by_reading(u'漢', u'かん')
    
#    q.clear_words()
#    q.add_words([{'word':u'建て替える', 'reading':u'たてかえる'},
#               {'word':u'漢字', 'reading':u'かんじ'},
#               {'word':u'漢字時代', 'reading':u'かんじじだい'},
#               {'word':u'漢字時代', 'reading':u'かんじじだいおおお'},
#               {'word':u'半分', 'reading':u'はんぶん'},
#               {'word':u'一つ', 'reading':u'ひとつ'}])
    
#    results = q.words_by_reading(u'人', u'ひと', tags=tags, index=2)
    
#    for word in results:
#        print word.word, word.reading
    tags = [SegmentTag.Dakuten, SegmentTag.Handakuten]
    id = reading_query.get_id(u'人', u'ひと')
    result = q.words_by_reading_id(id, tags=tags)
    for r in result:
        print r['word'], r['reading']
    print 'found', len(result)