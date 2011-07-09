# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

from segments import SegmentTag
import word_db
import reading_query
import word

word_t = None
segment_t = None
tag_t =  None


class WordQuery():
    
    def __init__(self, words_db_path):
        self.w_conn = word_db.get_connection(words_db_path)
        
    def Word(self, expr, reading):
        return word.Word(self.w_conn, expr, reading)
        
    def words_by_reading(self, char, reading, **kwargs):
        """Returns a list of Word objects composed of every word in the 
        solutions database that contains char with reading."""

        r_id = reading_query.get_id(char, reading)
        return self.words_by_reading_id(r_id, **kwargs)

    def words_by_reading_id(self, reading_id, **kwargs):
        """Returns a list of Word objects composed of every word in the 
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
        
        if index is not None:
            if index < 0:
                rindex = (index*-1)-1
                query = query.where(segment_t.c['indexr']==rindex)
            else:
                query = query.where(segment_t.c['index']==index)
        
        result = self.w_conn.execute(query, [r_id]).fetchall()
        return result


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


    def clear_words(self):
        """Remove all existing words from the database. """
    
        self.w_conn.execute('delete from word')

      
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