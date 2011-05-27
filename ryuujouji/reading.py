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

select_char = select([reading_t],
                     reading_t.c['character']==bindparam('character'))


solutions = []
def get_readings(word, reading):
    """Returns a list of dictionaries separating the word into portions of
    character-reading pairs that form the word."""
    
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
                if tools.is_kata(char) and tools.is_hira(reading[0]):
                    test_start = tools.hira_to_kata(reading[0])
                else:
                    test_start = reading[0]
            
                if char == test_start:
                    tmp_segments = copy.copy(segments)
                    tmp_segments.append({'character':char,
                                         'reading':char,
                                         'reading_id':0,
                                         'index':index})
                    index += 1
                    get_remaining_readings(word[1:], reading[1:],
                                           index, tmp_segments)
        else:
            char_readings = r_engine.execute(select_char,
                                             character=char).fetchall()

            #TODO: Handle non-kanji and non-kana characters
            if char_readings == None:
                print "Shouldn't be here for now."
                return None

            for cr in char_readings:              
                first_k = cr.reading[0]
                last_k = cr.reading[len(cr.reading)-1]

                variants = []
                oku_variants = []
                
                variants.append(cr.reading)
                
                
                if tools.has_dakuten(first_k):
                    d = tools.get_dakuten(first_k)
                    daku_r = d + cr.reading[1:]
                    if tools.is_kata(daku_r[0]):
                        daku_r = tools.kata_to_hira(daku_r)
                    variants.append(daku_r)
                                       
                if tools.has_handakuten(first_k):
                    d = tools.get_handakuten(first_k)
                    handaku_r = d + cr.reading[1:]
                    if tools.is_kata(handaku_r[0]):
                        handaku_r = tools.kata_to_hira(handaku_r)
                    variants.append(handaku_r)
                
                if last_k == u'つ' or last_k == u'ツ':
                    soku_r = cr.reading[:-1] + tools.get_sokuon(cr.reading[-1])
                    if tools.is_kata(soku_r[0]):
                        soku_r = tools.kata_to_hira(soku_r)
                    variants.append(soku_r)

                (r, s, o) = cr.reading.partition(".")
                rl = len(r)  #reading length (non-okurigana portion)
                ol = len(o)  #okurigana length
                #the portion of the known reading we want to test as okurigana
                word_oku = word[1:ol + 1]
                
                if o.endswith(u'る'):
                    ri_o = o[:-1] + u'り'
                    oku_variants.append(ri_o)
                                       
                for v in variants:
                    (r, s, o) = v.partition(".")
                    if tools.is_kata(r[0]):
                        r = tools.kata_to_hira(r)
                        
                    if o is not u'':    #has okurigana   
                        if r == reading[:rl] and o == word_oku:
                            tmp_segments = copy.copy(segments)
                            tmp_segments.append({'character':char+o,
                                             'reading':r+o,
                                             'reading_id':cr.id,
                                             'index':index})
                            index += rl+ol
                            get_remaining_readings(word[ol + 1:],
                                                   reading[ol + rl:],
                                                   index,
                                                   tmp_segments)
                        for ov in oku_variants:
                            if r == reading[:rl] and word_oku == ov:
                                tmp_segments = copy.copy(segments)
                                tmp_segments.append({'character':char+o,
                                                     'reading':r+o,
                                                     'reading_id':cr.id,
                                                     'index':index})
                                index += rl+ol
                                get_remaining_readings(word[ol + 1:],
                                                       reading[ol + rl:],
                                                       index,
                                                       tmp_segments)
                    else:
                        if reading.startswith(r):
                            tmp_segments = copy.copy(segments)
                            tmp_segments.append({'character':char,
                                                 'reading':r,
                                                 'reading_id':cr.id,
                                                 'index':index})
                            index += 1
                            get_remaining_readings(word[1:], reading[rl:],
                                                   index, tmp_segments)

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
    fill_solutions()
    print_stats()
#    dry_run()
#    testme(u'漢字', u'かんじ')
#    testme(u"小牛", u"こうし")
#    testme(u"バス停", u"バスてい")
#    testme(u"非常事態", u"ひじょうじたい")
#    testme(u"建て替える", u"たてかえる")
#    testme(u"小さい", u"ちいさい")
#    testme(u"鉄道公安官", u"てつどうこうあんかん")
#    testme(u"手紙", u"てがみ")
#    testme(u"筆箱", u"ふでばこ")
#    testme(u"人人", u"ひとびと")
#    testme(u"岸壁", u"がんぺき")
#    testme(u"一つ", u"ひとつ")
#    testme(u"別荘", u"べっそう")
#    testme(u"出席", u"しゅっせき")
#    testme(u"結婚", u"けっこん")
#    testme(u"分別", u"ふんべつ")   
#    testme(u"刈り手", u"かりて")    
#    testme(u"刈り入れ人", u"かりいれびと")
#    testme(u"日帰り", u"ひがえり")        
#    testme(u"アリドリ科", u"ありどりか")
 
    testme(u"イン腹ベビー", u"インはらベイビー")
    #testme(u"守り人", u"もりびと")
    #testme(u"糶り", u"せり")
    
    #testme(u"赤鷽", u"アカウソ")
    
#    testme(u"働き蟻", u"はたらきあり")
#    
    
#    testme(u"ヨウ素１２５", u"ようそひゃくにじゅうご")
#    testme(u"疾く疾く", u"とくとく")
#    testme(u"往き交い", u"いきかい")
    
    
    
    

#    testme(u"お腹", u"おなか")
##    testme(u"今日", u"きょう")





#    print "\n\n"

#p = pstats.Stats('pstats')
#p.sort_stats('time', 'cum').print_stats(.5)

#last attempt
#There are 161809 entries in JMdict. A solution has been found for 123150 of them. (76%)
#There are 161809 entries in JMdict. A solution has been found for 122567 of them. (75%)
#There are 161809 entries in JMdict. A solution has been found for 122506 of them. (75%)
#There are 161809 entries in JMdict. A solution has been found for 122286 of them. (75%)
#There are 161809 entries in JMdict. A solution has been found for 121805 of them. (75%)
#There are 161809 entries in JMdict. A solution has been found for 120073 of them. (74%)
#There are 161809 entries in JMdict. A solution has been found for 115877 of them. (71%)
#There are 161809 entries in JMdict. A solution has been found for 114528 of them. (70%)
#There are 161809 entries in JMdict. A solution has been found for 111607 of them. (68%)
#There are 161809 entries in JMdict. A solution has been found for 107847 of them. (66%)

