# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import tools
import copy

solutions = []
def get_readings(word, reading):
    """Returns a list of lists separating the word into portions of
    [character, reading] pairs that form the word."""
    
    global solutions
    solutions = []
    return min(get_remaining_readings(word, reading))


def get_remaining_readings(word, reading, segments=None):
    if segments == None: segments = []
    
    if len(word) == 0:
        solutions.append(segments)
    else:
        char = word[0]
        if tools.is_kana(char):
            if len(reading) != 0:
                if char == reading[0]:
                    tmp_segments = copy.copy(segments)
                    tmp_segments.append([char, char])
                    get_remaining_readings(word[1:], reading[1:], tmp_segments)
        else:
            char_readings = get_char_readings(char) 
         
            #TODO: Handle non-kanji and non-kana characters
            if char_readings == None:
                return None

            for cr in char_readings:
                has_oku = False
                if "." in cr:
                    has_oku = True
                if has_oku == True:
                     #reading, separator, okurigana
                    (r, s, o) = cr.partition(".")
                    
                    #trim - from affixes
                    if r[0] == '-':
                        r = r[1:]
                    if r[-1] == '-':
                        r = r[:-1]
                        
                    rl = len(r)  #reading length (non-okurigana portion)
                    ol = len(o)  #okurigana length
                    ot = word[1:ol + 1] #the portion we want to test as okurigana

                    if r == reading[:rl] and ot == o:
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append([char+o, r+o])
                        get_remaining_readings(word[ol + 1:], reading[ol + rl:], tmp_segments)
                else:
                  
                    if cr[0] == '-':
                        cr = cr[1:]
                    if cr[-1] == '-':
                        cr = cr[:-1]
                        
                    rl = len(cr)
                    #we deal with readings in hiragana, so convert from katakana if it exists
                    if tools.is_kata(cr[0]):
                        cr = tools.kata_to_hira(cr)

                    if reading.startswith(cr):
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append([char, cr])
                        get_remaining_readings(word[1:], reading[rl:], tmp_segments)
    return solutions

def get_char_readings(char):
    readings = []
    f = open('readings')
    in_kanji = False
    for reading in f:
        reading = reading.strip('\n')
        #kanji,sep,reading
        (k, s, r) = reading.partition(",")
        if k == char:
            in_kanji = True
            readings.append(unicode(r))
    
    return readings
    
def test_print_sol(readings):
    print
    for r in readings:
        print "Part: %s    Reading: %s" % (r[0], r[1])    
    
if __name__ == "__main__":
    test_print_sol(get_readings(u"小牛", u"こうし"))
    test_print_sol(get_readings(u"バス停", u"バスてい"))
    test_print_sol(get_readings(u"建て替える", u"たてかえる"))
    test_print_sol(get_readings(u"非常事態", u"ひじょうじたい"))    
    test_print_sol(get_readings(u"小さい", u"ちいさい"))
     