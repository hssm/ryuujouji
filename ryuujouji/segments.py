class SegmentTag:
    """Enums for types of transformations of readings."""
    Kana = 'Kana'
    Regular = 'Regular'
    Dakuten = 'Dakuten'
    Handakuten = 'Handakuten'
    Sokuon = 'Sokuon'
    KanaTrail = 'KanaTrail'
    OkuRegular = 'OkuRegular'
    OkuSokuon = 'OkuSokuon'
    OkuInflected = 'OkuInflected'

class Segment:
    """Class to hold segment information."""
    #A list of SegmentTags denoting the types of transformations of the reading.
    tags = None
    #The character we are solving
    character = None
    #The nth kanji in the word
    nth_kanji = None
    #Like nth_kanji, but nth from the right
    nth_kanjir = None
    #The dictionary reading of the character
    dic_reading = None
    #The database ID of the reading used to solve this segment
    reading_id = None
    #The reading of this segment as it appears in the word
    reading = None
    #The reading of this segment's okurigana as it appears in the word
    oku_reading = None
    
    def __init__(self, tag, character, dic_reading, reading_id, reading):
        self.tags = [tag]
        self.character = character
        self.dic_reading = dic_reading
        self.reading_id = reading_id
        self.reading = reading
        
    def append_oku(self, oku, orig):
        self.oku_reading = oku
        self.dic_reading += u'.%s' % orig