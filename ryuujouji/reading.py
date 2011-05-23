# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import cProfile
import pstats
import time
import copy
from sqlalchemy.sql import select, and_, or_

import tools
import db

meta = db.get_meta()
meta.reflect()
reading_t = meta.tables['reading']
word_t = meta.tables['word']
solution_t = meta.tables['solution']
segment_t = meta.tables['segment']
r_engine = meta.bind


solutions = []
def get_individual_readings(word, reading):
    global solutions
    solutions = []
    return get_remaining_readings(word, reading)


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
                    tmp_segments.append([char, char, 0, 0, 'kana'])
                    get_remaining_readings(word[1:], reading[1:], tmp_segments)
        else:
            s = select([reading_t.c['reading'], reading_t.c['has_okurigana']],
                       reading_t.c['character'] == char)

            char_readings = r_engine.execute(s).fetchall()

            #TODO: Handle non-kanji and non-kana characters
            if char_readings == None:
                return None

            for cr in char_readings:
                if cr.has_okurigana == True:
                    (r, s, o) = cr.reading.partition(".") #reading, separator, okurigana

                    rl = len(r)  #reading length (non-okurigana portion)
                    ol = len(o)  #okurigana length
                    ot = word[1:ol + 1] #the portion we want to test as okurigana

                    if r == reading[:rl] and ot == o:
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append([char+o, r+o, 0, 0, 'kanji (%s) with okurigana (%s)'% (r,o)])
                        get_remaining_readings(word[ol + 1:], reading[ol + rl:], tmp_segments)
                else:
                    r = cr.reading
                    rl = len(r)
                    #we deal with readings in hiragana, so convert from katakana if it exists
                    if tools.is_kata(r[0]):
                        r = tools.kata_to_hira(r)

                    if reading.startswith(r):
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append([char, r, 0, 0, 'kanji'])
                        get_remaining_readings(word[1:], reading[rl:], tmp_segments)
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

