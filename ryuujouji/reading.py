# -*- coding: utf-8 -*-

import sys
import os
import re
import tools
import copy

from sqlalchemy.sql import select, and_, or_

import tools
import db

class Segment():
    unit = None
    reading = None
    reading_id = None
    info = None
    index = 0
    
    def __init__(self, unit, reading, reading_id, index, info=''):
        self.unit = unit
        self.reading = reading
        self.reading_id = reading_id
        self.index = index
        self.info = info

indent = ''
meta = db.get_meta()
meta.reflect()
reading_t = meta.tables['reading']
word_t = meta.tables['word']
solution_t = meta.tables['solution']
segment_t = meta.tables['segment']

r_engine = meta.bind
def get_individual_readings(word, reading, segments=None, found=None, solutions=None):
    
    if solutions == None: solutions = []
    if found == None: found = ""
    if segments == None: segments = []
    
    if len(word) == 0:
#        print "Nothing left to solve. Appending this one as a solution."
        solutions.append(segments)
#    else:
#        print "\nSolving: %s  ==  %s          <--> Root: %s" % (word, reading, found)

    #for char in word:
    if len(word) > 0:
        char = word[0]
        if tools.is_kana(char):
            #if ord(char) in KATAKANA_RANGE:
            #    char = tools.kata_to_hira(char)
            if len(reading) == 0:
                pass
#                print "No readings left to match. Part of word left: ", word
            else:
                if char == reading[0]:
#                    print "--> Removed:  " + char
                    tmp_found = found + char
                    tmp_word = word[1:]
                    tmp_reading = reading[1:]
                    tmp_segments = copy.copy(segments)
                    tmp_segments.append(Segment(char, char, 0, 0, 'kana'))
                    get_individual_readings(tmp_word, tmp_reading, tmp_segments,
                                            tmp_found, solutions)
#                else:
 #                   print "%s is definitely not %s. Abort attempt." % (char, reading[0])
        else:
            s = select([reading_t], reading_t.c['character'] == char)
            char_readings = r_engine.execute(s).fetchall()

#            print "0th character is a kanji: = " + char

            if char_readings == None:    #TODO: Handle non-kanji and non-kana characters
#                print "Need to abort gracefully!"
                return None
#            for r in char_readings:
#                print indent + "\t" + r.reading + "\t\t" + r.affix

            for cr in char_readings:
                #print "     " + r.reading + \t + r.affix + \t + str(r.has_okurigana)

                if cr.has_okurigana == True:
                    (r, s, o) = cr.reading.partition(".") #reading, separator, okurigana


                    rl = len(r)
                    ol = len(o)
                    ot = word[1:ol + 1] #the portion we want to test as okurigana

                    if r == reading[:rl] and ot == o:
#                        print "Match found for reading %s with okurigana %s" % (r, o)
                        tmp_found = found + r + o
                        tmp_word = word[ol + 1:]
                        tmp_reading = reading[ol + rl:]
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append(Segment(char, r, 0, 0, 'kanji with okurigana (%s)'%o))
                        tmp_segments.append(Segment(o, o, 0, 0, 'okurigana'))
                        get_individual_readings(tmp_word, tmp_reading, tmp_segments, tmp_found, solutions)
                else:
                    r = cr.reading
                    rl = len(r)
                    #we deal with readings in hiragana, so convert from katakana if it exists
                    if tools.is_kata(r[0]):
                        r = tools.kata_to_hira(r)

                    if reading.startswith(r):
#                        print "Match found for reading %s: starting with %s" % (reading, r)
                        tmp_found = found + r
                        tmp_word = word[1:]
                        tmp_reading = reading[rl:]
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append(Segment(char, r, 0, 0, 'kanji'))
                        get_individual_readings(tmp_word, tmp_reading, tmp_segments, tmp_found, solutions)
#            print "No further parsing possible for reading starting with %s and ending with %s.\n     Up one level." % (found, word)
    return solutions

solution_l = []
segment_l = []

def fill_solutions():
    sol_id = 0
    
    s = select([word_t])
    words = r_engine.execute(s)
    for word in words:
        print "STARTING THIS WORD ==============>", word.keb, word.reb
        solutions = get_individual_readings(word.keb, word.reb)
        for s in solutions:
            sol_id +=1
            solution_l.append({'id':sol_id, 'word_id':word.id})
            for seg in s:
                #print 'seg == ' , seg.unit
                segment_l.append({'solution_id':sol_id,
                                  'reading_id':seg.reading_id,
                                  'index':seg.index})
    r_engine.execute(solution_t.insert(), solution_l)
    r_engine.execute(segment_t.insert(), segment_l)
    
                
    
    
if __name__ == "__main__":

    fill_solutions()
    #db_populate_words_by_reading()

#    solutions = get_individual_readings(u"小牛", u"こうし")
#    solutions = get_individual_readings(u"お腹", u"おなか")
#    solutions = get_individual_readings(u"バス停", u"バスてい")
#    solutions = get_individual_readings(u"一つ", u"ひとつ")
#    solutions = get_individual_readings(u"非常事態", u"ひじょうじたい")
#    solutions = get_individual_readings(u"建て替える", u"たてかえる")
#    solutions = get_individual_readings(u"今日", u"きょう")
#    solutions = get_individual_readings(u"小さい", u"ちいさい")
#    solutions = get_individual_readings(u"鉄道公安官", u"てつどうこうあんかん")
#    solutions = get_individual_readings(u"日帰り", u"ひがえり")
#    print "\n\n"
#    for i,sol in enumerate(solutions):
#        print "Solution #", i
#        for seg in sol:
#             print "%s -- %s  -- %s" % (seg.unit, seg.reading, seg.info)
#    db_populate_words_by_reading()
