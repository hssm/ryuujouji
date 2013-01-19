# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import word_db
import reading_query
from word import Word

word_t = None
segment_t = None
tag_t =  None


class WordQuery():
    
    def __init__(self, words_db_path):
        self.conn = word_db.get_connection(words_db_path)
        
    def Word(self, expr, reading):
        return Word(self.conn, expr, reading)
        
    def words_by_reading(self, char, reading, **kwargs):
        """Returns a list of Word objects composed of every word in the 
        solutions database that contains char with reading."""

        r_id = reading_query.get_id(char, reading)
        return self.words_by_reading_id(r_id, **kwargs)

    def words_by_reading_id(self, reading_id, **kwargs):
        """Returns a list of Word objects composed of every word in the 
        solutions database that contains reading_id."""
        
        query = '''
SELECT word, reading
FROM word
JOIN segment ON segment.word_id = word.id AND segment.reading_id=? 
                '''       
        
        results = self.conn.execute(query, [reading_id]).fetchall()

        word_list = []
        for r in results:
            word_list.append(Word(self.conn, r['word'], r['reading']))
        return word_list

    def contains_char(self, char, **kwargs):
        """Returns a list of Word objects composed of every word in the 
        solutions database that contains char."""
    
        count = kwargs.get('count', 1)
        word_list = []
        
        in_keb = '%%'
        if count > 0:
            for n in range(0, count):
                in_keb += '%s%%' % char
            s = 'select word, reading from word where word.word like ?' 
            
            results = self.conn.execute(s, [in_keb]).fetchall()
            for r in results:
                word_list.append(Word(self.conn, r['word'], r['reading']))
        return word_list

    def clear_words(self):
        """Remove all existing words from the database."""
    
        self.conn.execute('delete from word')

      
if __name__ == '__main__':
    #dbpath = 'dbs/test_query.sqlite'
    dbpath = 'dbs/jmdict_solutions.sqlite'
    #word_db.create_db(dbpath)
    q = WordQuery(dbpath)
#    words = q.contains_char(u'帰')
#    for w in words:
#        print w.word, w.reading
    
    id = reading_query.get_id(u'帰', u'かえ.る')
    words = q.words_by_reading_id(id)
    for w in words:
        print w.word, w.reading
    print 'found', len(words)