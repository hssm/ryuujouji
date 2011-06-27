import reading_query
import solver
import segments

class Word():
    
    word = None
    reading = None
    solved = None
    segments = []
    
    def __init__(self, conn, word, reading):
        self.conn = conn
        self.word = word
        self.reading = reading
        
        row = self.get_word(word, reading)
        
        if row is None:
            seglist = solver.solve_reading(word, reading)
        else:
            seglist = self.get_segments(row)
        
        self.segments = seglist 
        

        
    def get_word(self, word, reading):
        """Returns the database row (as a tuple) for word with reading. If the
        word/reading combination doesn't exist, returns None."""
        
        s = "select * from word where word=? and reading=?"
        return self.conn.execute(s, [word, reading]).fetchone()

            
    def get_segments(self, word_row):
        word_id = word_row['id']
        s = 'select * from segment where segment.word_id=?'
        segments = self.conn.execute(s, [word_id]).fetchall()
        ss = []
        for seg_row in segments:
            ss.append(self.segment_from_row(seg_row))
        return ss
    
    def segment_from_row(self, row):
       pass