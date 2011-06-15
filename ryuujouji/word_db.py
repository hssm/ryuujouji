import os
from sqlalchemy import (create_engine, Table, Column, Unicode,
                        UniqueConstraint, Enum, Integer, ForeignKey, MetaData)

class InvalidDatabaseException(Exception): pass

class SolveTag:
    """String enums for the status of a word's solution."""
    Solved = 'Solved'
    Unsolvable = 'Unsolvable'
    Unchecked = 'Unchecked'
    

meta = MetaData()

word_t = Table('word', meta,
               Column('id', Integer, primary_key=True),
               Column('word', Unicode, index=True),
               Column('reading', Unicode, index=True),
               Column('solved', Enum(SolveTag.Solved, SolveTag.Unsolvable,
                                    SolveTag.Unchecked),
                      default=SolveTag.Unchecked),
               UniqueConstraint('word', 'reading'))

segment_t = Table('segment', meta,
                   Column('id', Integer, primary_key=True, autoincrement=False),
                   Column('word_id', Integer, ForeignKey('word.id')),
                   Column('reading_id', Integer),
                   Column('index', Integer),
                   Column('indexr', Integer))

tag_t = Table('tag', meta,
               Column('id', Integer, primary_key=True),
               Column('segment_id', Integer, ForeignKey('segment.id')),
               Column('tag', Integer, default=False))

    
def create_db(db_path):
    """Creates a new word database and returns a WordsDB object for it. If
    db_path already exists, it is overwritten with a new database."""
    
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_engine('sqlite:///' + db_path)
    meta.create_all(engine)
    
    return engine.connect()


def get_connection(db_path):
    """Returns a connection to the given database."""
    
    if not os.path.exists(db_path):
        raise InvalidDatabaseException("No such database: %s" % db_path)
    engine = create_engine('sqlite:///' + db_path)
    return engine.connect()