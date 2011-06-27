class SegmentTag:
    """Enums for types of transformations of readings."""
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
    tags = []
    #The character we are solving
    character = None
    #The nth kanji in the word
    index = None
    #Like nth_kanji, but nth from the right
    indexr = None
    #The dictionary reading of the character
    dic_reading = None
    #The database ID of the reading used to solve this segment
    reading_id = None
    #The reading of this segment as it appears in the word
    reading = None
    #The reading of this segment's okurigana as it appears in the word
    oku_reading = None
    #If the segment holds a kanji character (instead of kana)
    is_kanji = None
    
    def __init__(self, tags, character, dic_reading, reading_id, reading):
        if tags is not None:
            self.tags = [tags]
            self.is_kanji = True
        else:
            self.tags = []
            self.is_kanji = False
            
        self.character = character
        self.dic_reading = dic_reading
        self.reading_id = reading_id
        self.reading = reading
