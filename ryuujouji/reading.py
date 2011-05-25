# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

#import cProfile
#import pstats
import time
import copy
from sqlalchemy.sql import select, and_, or_, bindparam

import tools
import db

meta = db.get_meta()
meta.reflect()
reading_t = meta.tables['reading']
word_t = meta.tables['word']
segment_t = meta.tables['segment']
r_engine = meta.bind

select_char = select([reading_t], reading_t.c['character']==bindparam('character'))


solutions = []
def get_readings(word, reading):
    """Returns a list of lists separating the word into portions of
    [character, reading] pairs that form the word."""
    
    global solutions
    solutions = []
    results = get_remaining_readings(word, reading)
    if len(results) > 0:
        return min(results, key=len)
    else:
        return []


def get_remaining_readings(word, reading, index=0, segments=None):
    
    if segments == None:
        segments = []

    if len(word) == 0:
        solutions.append(segments)
    else:
        char = word[0]
        if tools.is_kana(char):
            if len(reading) != 0:
                if char == reading[0]:
                    tmp_segments = copy.copy(segments)
                    tmp_segments.append({'character':char, 'reading':char, 'reading_id':0, 'index':index})
                    index += 1
                    get_remaining_readings(word[1:], reading[1:], index, tmp_segments)
        else:
            char_readings = r_engine.execute(select_char, character=char).fetchall()

            #TODO: Handle non-kanji and non-kana characters
            if char_readings == None:
                print "Shouldn't be here for now."
                return None

            for cr in char_readings:
                #check for possible rendaku branch
#                print cr.reading
                first_k = cr.reading[0]
                try_ren = False
                if tools.has_dakuten(first_k):
                    d = tools.get_dakuten(first_k)
                    new_r = cr.reading
                    new_r = d + new_r[1:]
                    try_ren = True
                                       
                    
#                if tools.has_handakuten(first_k):
#                    print 'h', first_k
               

                if cr.has_okurigana == True:
                    (r, s, o) = cr.reading.partition(".") #reading, separator, okurigana

                    rl = len(r)  #reading length (non-okurigana portion)
                    ol = len(o)  #okurigana length
                    ot = word[1:ol + 1] #the portion we want to test as okurigana

                    if r == reading[:rl] and ot == o:
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append({'character':char+o, 'reading':r+o, 'reading_id':cr.id, 'index':index})
                        index += rl+ol
                        get_remaining_readings(word[ol + 1:], reading[ol + rl:], index, tmp_segments)
#                    elif try_ren:
#                        if r == new_r and ot == o:   #if the original reading failed, try a rendaku version
#                            tmp_segments = copy.copy(segments)
#                            tmp_segments.append({'character':char+o, 'reading':new_r+o, 'reading_id':cr.id, 'index':index})
#                            index += rl+ol
#                            get_remaining_readings(word[ol + 1:], reading[ol + rl:], index, tmp_segments)
                        
                        
                else:
                    r = cr.reading
                    rl = len(r)
                    #we deal with readings in hiragana, so convert from katakana if it exists
                    if tools.is_kata(r[0]):
                        r = tools.kata_to_hira(r)

                    if reading.startswith(r):                      
                        tmp_segments = copy.copy(segments)
                        tmp_segments.append({'character':char, 'reading':r, 'reading_id':cr.id, 'index':index})
                        index += 1
                        get_remaining_readings(word[1:], reading[rl:], index, tmp_segments)
                    elif try_ren:
                        if reading.startswith(new_r):     #if the original reading failed, try a rendaku version
                            tmp_segments = copy.copy(segments)
                            tmp_segments.append({'character':char, 'reading':r, 'reading_id':cr.id, 'index':index})
                            index += 1
                            get_remaining_readings(word[1:], reading[rl:], index, tmp_segments)
    return solutions

found_l = []
segment_l = []

def fill_solutions():
    start = time.time()
    r_engine.execute(segment_t.delete())
    s = select([word_t])
    words = r_engine.execute(s)
    i = 0
    for word in words:
#        i += 1
#        if i == 10000:
#            break
        segments = get_readings(word.keb, word.reb)
        for seg in segments:
            #print 'seg == ' , seg.unit
            found_l.append({'word_id':word.id, 'found':True})
            segment_l.append({'word_id':word.id,
                              'reading_id':seg['reading_id'],
                              'index':seg['index']})
    print "Saving..."
    u = word_t.update().where(word_t.c['id']==bindparam('word_id')).values(found=bindparam('found'))
    r_engine.execute(u, found_l)
    r_engine.execute(segment_t.insert(), segment_l)
    print 'took %s seconds' % (time.time() - start)

def dry_run():
    """Don't save any changes to the database, but check if the present
     parsing behaviour breaks the solving of an already-solved entry.
     """
     
    start = time.time()
    r_engine.execute(segment_t.delete())
    s = select([word_t])
    words = r_engine.execute(s)
    newly_solved = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        if word.found == True:
            if len(segments) == 0:
                print "Regression for word %s " % word.keb
        else:
            if len(segments) > 0:
                newly_solved += 1
    print "The changes will solve another %s entries. " % newly_solved


def print_stats():
    s = select([word_t])
    words = r_engine.execute(s).fetchall()
    n = len(words)
    
    s = select([word_t], word_t.c['found'] == True)
    found = r_engine.execute(s).fetchall()
    nf = len(found)
    
    percent = float(nf) / float(n) * 100
    print "There are %s entries in JMdict. A solution has been found for %s"\
          " of them. (%d%%)" % (n, nf, percent)

def testme(k, r):
    print
    print "Solving: %s == %s" % (k, r)
    segments = get_readings(k, r)

    for s in segments:
        print "%s -- %s  --  %s [index]" % (s['character'], s['reading'],
                                             s['index'])
                
if __name__ == "__main__":
#    cProfile.run('fill_solutions()', 'pstats')
#    fill_solutions()
    print_stats()
#    dry_run()
#    testme(u'漢字', u'かんじ')
#    testme(u"小牛", u"こうし")
##    testme(u"お腹", u"おなか")
#    testme(u"バス停", u"バスてい")
##    testme(u"一つ", u"ひとつ")
#    testme(u"非常事態", u"ひじょうじたい")
#    testme(u"建て替える", u"たてかえる")
##    testme(u"今日", u"きょう")
#    testme(u"小さい", u"ちいさい")
#    testme(u"鉄道公安官", u"てつどうこうあんかん")
##    testme(u"日帰り", u"ひがえり")
#    testme(u"活を求める", u"かつをもとめる")
#    testme(u"守り人", u"もりびと")
    testme(u"手紙", u"てがみ")
    testme(u"筆箱", u"ふでばこ")
#    testme(u"刈り入れ人", u"かりいれびと")
    testme(u"人人", u"ひとびと")

#    print "\n\n"

#p = pstats.Stats('pstats')
#p.sort_stats('time', 'cum').print_stats(.5)

#last attempt
#There are 161809 entries in JMdict. A solution has been found for 111607 of them. (68%)
#There are 161809 entries in JMdict. A solution has been found for 107847 of them. (66%)

