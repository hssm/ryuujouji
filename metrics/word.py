# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import solver
from sqlite3 import IntegrityError

class Word():
    
    def __init__(self, conn, word, reading):
        self.conn = conn
        self.word = word
        self.reading = reading

        row = self.__get_word(word, reading)
        
        if row is None:
            self.known = False
            self.id = None
        else:
            self.known = True
            self.id = row['id']
            
        self.segments = solver.solve(word, reading)
        if self.segments is None:
            self.solved = False
        else:
            self.solved = True
                
    def __get_word(self, word, reading):
        """Returns the database row (as a tuple) for word with reading. If the
        word/reading combination doesn't exist, returns None."""
        
        s = "select * from word where word=? and reading=?"
        return self.conn.execute(s, [word, reading]).fetchone()

    def save(self):
        """Saves the word to the database. You still need to call commit
        externally to store the changes."""
        c = self.conn.cursor()
        
        word_ins = 'insert into word(word, reading, solved) values(?,?,?)'
        seg_ins = "insert into segment(word_id, reading_id, character, 'index',"\
                  "indexr) values (?,?,?,?,?)"
        tag_ins = "insert into tag(segment_id, tag) values(?,?)"
        
        try:
            c.execute(word_ins, [self.word, self.reading, self.solved])
            word_id = c.lastrowid
            
            if self.segments is not None:
                for s in self.segments:
                    c.execute(seg_ins,
                              [word_id, s.reading_id, s.character, s.index,
                               s.indexr])
                    segment_id = c.lastrowid
                
                    for tag in s.tags:
                        c.execute(tag_ins, [segment_id, tag])
        
        #We don't want to try inserting segments and tags if the word
        #already exists in the database (because they will already be there).
        except IntegrityError:
            pass

        
    def delete(self, word, reading):
        """Remove this word from the database. You still need to call commit
        externally to store the changes."""

        if self.id is not None:
            self.conn.execute('delete from word where id=?', self.id)
            