import sqlite3
import reading_db
import tools

conn = reading_db.get_connection()

def get_id(char, reading):
    """Returns the database id of the reading of char. Reading can be either
    hiragana or katakana (on or kun readings can be found with either)."""
    
    if len(reading) == 0:
        return None

    conn.row_factory = sqlite3.Row
    #Get both the hiragana and katakana form of reading
    if tools.is_kata(reading[0]):
        k_reading = reading
        h_reading = tools.kata_to_hira(reading)
    else:
        h_reading = reading
        k_reading = tools.hira_to_kata(reading)
           
    s = 'SELECT * FROM reading WHERE character=? and (reading=? or reading=?)'
    result = conn.execute(s, [char, h_reading, k_reading]).fetchall()
    if len(result) <= 0:
        return None
    else:
        return result[0]['id']
    
def row_by_id(id):
    
    s = 'select * from reading where id=?'
    return conn.execute(s, [id]).fetchall()