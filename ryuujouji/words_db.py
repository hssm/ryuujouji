import os
from sqlalchemy import create_engine, Table, Column, Unicode, UniqueConstraint,\
                       Boolean, Integer, ForeignKey, MetaData

words_path = None

s_meta = MetaData()
s_engine = None

word_t = Table('word', s_meta,
               Column('id', Integer, primary_key=True),
               Column('word', Unicode, index=True),
               Column('reading', Unicode, index=True),
               Column('found', Boolean, default=False, nullable=True),
               UniqueConstraint('word', 'reading')
               )

segment_t = Table('segment', s_meta,
                   Column('id', Integer, primary_key=True, autoincrement=False),
                   Column('word_id', Integer, ForeignKey('word.id')),
                   Column('reading_id', Integer),
                   Column('index', Integer),
                   Column('indexr', Integer))

tag_t = Table('tag', s_meta,
               Column('id', Integer, primary_key=True),
               Column('segment_id', Integer, ForeignKey('segment.id')),
               Column('tag', Integer, default=False))


def init():
    s_engine = create_engine('sqlite:///' + words_path)
    s_meta.create_all(s_engine)


def get_connection():
    if not os.path.exists(words_path):
        init()
    engine = create_engine('sqlite:///' + words_path)
    return engine.connect()


if __name__ == "__main__":
    try:
        os.remove(words_path)
    except:
        pass
    init()