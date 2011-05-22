# -*- coding: utf-8 -*-

import cProfile
import pstats
import time
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
def get_individual_readings(word, reading, segments=None, solutions=None):
    
    if solutions == None: solutions = []
    if segments == None: segments = []
    
    if len(word) == 0:
        solutions.append(segments)

    #for char in word:
    if len(word) > 0:
        char = word[0]
        if tools.is_kana(char):
            if len(reading) != 0:
                if char == reading[0]:
                    tmp_word = word[1:]
                    tmp_segments = copy.copy(segments)
                    tmp_segments.append([char, char, 0, 0, 'kana'])
                    get_individual_readings(tmp_word, reading[1:], tmp_segments,
                                            solutions)
        else:
            s = select([reading_t.c['reading'], reading_t.c['has_okurigana']],
                       reading_t.c['character'] == char)

            char_readings = r_engine.execute(s).fetchall()

            if char_readings == None:    #TODO: Handle non-kanji and non-kana characters
                return None

            for cr in char_readings:

                if cr.has_okurigana == True:
                    (r, s, o) = cr.reading.partition(".") #reading, separator, okurigana

                    rl = len(r)  #reading length (non-okurigana portion)
                    ol = len(o)  #okurigana length
                    ot = word[1:ol + 1] #the portion we want to test as okurigana

                    if r == reading[:rl] and ot == o:
                        tmp_word = word[ol + 1:]
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append([char+o, r+o, 0, 0, 'kanji (%s) with okurigana (%s)'% (r,o)])
                        get_individual_readings(tmp_word, reading[ol + rl:], tmp_segments, solutions)
                else:
                    r = cr.reading
                    rl = len(r)
                    #we deal with readings in hiragana, so convert from katakana if it exists
                    if tools.is_kata(r[0]):
                        r = tools.kata_to_hira(r)

                    if reading.startswith(r):
                        tmp_word = word[1:]
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append([char, r, 0, 0, 'kanji'])
                        get_individual_readings(tmp_word, reading[rl:], tmp_segments, solutions)
    return solutions

solution_l = []
segment_l = []

def fill_solutions():
    sol_id = 0
    start = time.time()
    s = select([word_t])
    words = r_engine.execute(s)
    i = 0
    for word in words:
#        i += 1
#        if i == 10000:
#            break
#       print "STARTING THIS WORD ==============>", word.keb, word.reb
        solutions = get_individual_readings(word.keb, word.reb)
        for s in solutions:
            sol_id +=1
            solution_l.append({'id':sol_id, 'word_id':word.id})
            for seg in s:
                #print 'seg == ' , seg.unit
                segment_l.append({'solution_id':sol_id,
                                  'reading_id':seg[2],
                                  'index':seg[3]})
    print 'took %s seconds' % (time.time() - start)
    #r_engine.execute(solution_t.insert(), solution_l)
    #r_engine.execute(segment_t.insert(), segment_l)
    
    
                

def testme(k, r):
    print
    print "Solving: %s == %s" % (k, r)
    solutions = get_individual_readings(k, r)
    for i,sol in enumerate(solutions):
        print "Solution #", i
        for sol in sol:
            print "%s -- %s  -- %s" % (sol[0], sol[1], sol[4])
                
if __name__ == "__main__":
#    cProfile.run('fill_solutions()', 'pstats')
#    fill_solutions()

    testme(u"小牛", u"こうし")
#    testme(u"お腹", u"おなか")
    testme(u"バス停", u"バスてい")
#    testme(u"一つ", u"ひとつ")
    testme(u"非常事態", u"ひじょうじたい")
    testme(u"建て替える", u"たてかえる")
#    testme(u"今日", u"きょう")
    testme(u"小さい", u"ちいさい")
#    testme(u"鉄道公安官", u"てつどうこうあんかん")
#    testme(u"日帰り", u"ひがえり")
#    print "\n\n"

#p = pstats.Stats('pstats')
#p.sort_stats('time', 'cum').print_stats(.5)

