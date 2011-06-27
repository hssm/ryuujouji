import sqlite3
import os

class InvalidDatabaseException(Exception): pass

class SolveTag:
    """String enums for the status of a word's solution."""
    Solved = 'Solved'
    Unsolvable = 'Unsolvable'
    Unchecked = 'Unchecked'
    
def create_db(db_path):
    """Creates a new word database and returns a WordsDB object for it. If
    db_path already exists, it is overwritten with a new database."""
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print 'Removed existing database at %s' % db_path

     
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    table = '''
        CREATE TABLE word(
            id       INTEGER PRIMARY KEY,
            word     TEXT,
            reading  TEXT,
            solved   TEXT DEFAULT %s,
            UNIQUE(word, reading) ON CONFLICT IGNORE
        )
        ''' % SolveTag.Unchecked    
    c.execute(table)
    c.execute('CREATE INDEX word_idx ON word(word)')
    c.execute('CREATE INDEX reading_idx ON word(reading)')

    table = '''
        CREATE TABLE segment(
            id          INTEGER PRIMARY KEY,
            word_id     INTEGER,
            reading_id  TEXT,
            character   TEXT,
            'index'     INTEGER,
            indexr      INTEGER,
            dic_reading TEXT,
            reading     TEXT,
            oku_reading TEXT,
            is_kanji    BOOLEAN,
            FOREIGN KEY (word_id) REFERENCES word(id)
        )
        '''
    c.execute(table)
    
    table = '''
        CREATE TABLE tag(
            id             INTEGER PRIMARY KEY,
            segment_id     INTEGER,
            tag            TEXT,
            FOREIGN KEY (segment_id) REFERENCES segment(id)
        )
        '''
    c.execute(table)


def get_connection(db_path):
    """Returns a connection to the given database."""
    
    if not os.path.exists(db_path):
        raise InvalidDatabaseException("No such database: %s" % db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn