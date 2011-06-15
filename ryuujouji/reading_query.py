import reading_db
import tools
from sqlalchemy.sql import select, and_, or_

r_conn = reading_db.get_connection()
reading_t = reading_db.reading_t

def get_id(char, reading):
    """Returns the database id of the reading of char. Reading can be either
    hiragana or katakana (on or kun readings can be found with either)."""
    
    if len(reading) == 0:
        return None
    
    #Get both the hiragana and katakana form of reading
    if tools.is_kata(reading[0]):
        k_reading = reading
        h_reading = tools.kata_to_hira(reading)
    else:
        h_reading = reading
        k_reading = tools.hira_to_kata(reading)
        
    s = select([reading_t], and_(reading_t.c['character']==char,
                                 or_(reading_t.c['reading']==h_reading,
                                     reading_t.c['reading']==k_reading)))
    result = r_conn.execute(s).fetchall()
    if len(result) <= 0:
        return None
    else:
        return result[0].id