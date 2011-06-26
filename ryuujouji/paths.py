import os

filedir = os.path.dirname(__file__)
db_path = os.path.join(filedir, 'dbs')

READINGS_PATH = os.path.join(db_path, 'readings.sqlite')
KANJIDIC_PATH = os.path.join(db_path, 'kanjidic.sqlite')
OTHER_READINGS_PATH = os.path.join(db_path, 'other_readings')