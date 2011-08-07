class SegmentTag:
    """Enums for types of transformations of readings."""
    Regular = 'Regular'
    Dakuten = 'Dakuten'
    Handakuten = 'Handakuten'
    Sokuon = 'Sokuon'
    OkuRegular = 'OkuRegular'
    OkuSokuon = 'OkuSokuon'
    OkuInflected = 'OkuInflected'

class Segment:
    """Class to hold segment information."""
    
    def __init__(self, tags, character, dic_reading, reading_id, reading,
                 grapheme):
        if tags is not None:
            tags = tags
            is_kanji = True
        else:
            tags = []
            is_kanji = False
        
        
        #A list of SegmentTags denoting the types of transformations of the
        #reading.
        self.tags = tags
        #The character we are solving
        self.character = character
        #The nth kanji in the word
        self.index = None
        #Like nth_kanji, but nth from the right
        self.indexr = None
        #The dictionary reading of the character
        self.dic_reading = dic_reading
        #The database ID of the reading used to solve this segment
        self.reading_id = reading_id
        #The grapheme of this segment
        self.grapheme = grapheme
        #The reading of this segment
        self.reading = reading
        #If the segment holds a kanji character (instead of kana)
        self.is_kanji = is_kanji
        


    def __str__(self):
        return 'Segment[%s, %s]' % (self.character, self.reading)