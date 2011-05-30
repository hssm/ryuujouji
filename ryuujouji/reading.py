# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import cProfile
import pstats
import time
import copy
from sqlalchemy.sql import select, and_, or_, bindparam

import tools
import db

class SegmentTag:
    """Enums for types of transformations of readings."""
    Kana, Regular, Dakuten, Handakuten, Sokuon, Kana_trail = range(6)

class SegmentOkuTag:
    """Enums for types of transformations of Okurigana."""
    Regular, Sokuon, Inflected = range(3)

class Segment:
    """Class to hold segment information."""
    #A SegmentTag denoting the type of transformation of the reading.
    tag = None
    #The character we are solving
    character = None
    #the nth character in the word that this segment starts at
    index = None
    #the dictionary reading of the character
    dic_reading = None
    #the database ID of the reading used to solve this segment
    reading_id = None
    #the reading of this segment as it appears in the word
    reading = None
    #A description of the transformation (showing specific character changes)
    info = None
    #A SegmentOku object with information on the reading's Okurigana
    oku_segment = None
    
    def __init__(self, tag, character, index, dic_reading, reading_id,
                 reading, info):
        self.tag = tag
        self.character = character
        self.index = index
        self.dic_reading = dic_reading
        self.reading_id = reading_id
        self.reading = reading
        self.info = info

class SegmentOku:
    #A SegmentOkuTag denoting the type of transformation of the reading.
    tag = None
    #the reading of this segment as it appears in the word
    reading = None    
    #A description of the transformation (showing specific character changes)
    info = None
    
    def __init__(self, tag, reading, info):
        self.tag = tag
        self.reading = reading
        self.info = info

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
    
    #FIXME: This solution is ugly and produces unexpected behaviour
    #(modifying input word). This should be done properly below.
    #replace all 々 with their respective kanji
    if word[0] != u'々': #it could be just that character and its name(s)
        for i,k in enumerate(word):
            if k == u'々':
                word = word.replace(u'々', word[i-1], 1)
    
    solutions = solve_reading(word, reading)
    if len(solutions) > 0:
        return min(solutions, key=len)
    else:
        return []

def solve_kana(char, word, reading, index, segments):
    if len(reading) != 0:
        if tools.is_kata(char) and tools.is_hira(reading[0]):
            test_start = tools.hira_to_kata(reading[0])
        else:
            test_start = reading[0]
    
        if char == test_start:
            s = Segment(SegmentTag.Kana, char, index, char, 0, reading[0], 'Kana')
            tmp_segments = copy.copy(segments)
            tmp_segments.append(s)
            index += 1
            solve_reading(word[1:], reading[1:], index, tmp_segments)

def solve_character(char, word, reading, index, segments):
    char_readings = r_engine.execute(select_char, character=char).fetchall()

    #TODO: Handle non-kanji and non-kana characters
    if char_readings == None:
        print "Shouldn't be here for now."
        return None

    for cr in char_readings:
        variants = []
        oku_variants = []
       
        (r, s, o) = cr.reading.partition(".")
        rl = len(r)  #reading length (non-okurigana portion)
        ol = len(o)  #okurigana length

        s = Segment(SegmentTag.Regular, char, index, cr.reading, cr.id,
                    reading[:rl+ol], 'Regular character reading: '+cr.reading)
        variants.append([cr.reading, s])
        
        first_k = r[0]
        last_k = r[len(r)-1]
        
        if tools.has_dakuten(first_k):
            d = tools.get_dakuten(first_k)
            daku_r = d + cr.reading[1:]
            info = 'Dakuten (゛) added to first syllable in reading. '\
                    '%s became %s.' % (cr.reading[:rl], daku_r)
            s = Segment(SegmentTag.Dakuten, char, index, cr.reading, cr.id,
                        reading[:rl+ol], info)
            variants.append([daku_r, s])
                               
        if tools.has_handakuten(first_k):
            d = tools.get_handakuten(first_k)
            handaku_r = d + cr.reading[1:]
            info = 'Handakuten (゜) added to first syllable in reading. '\
                    '%s became %s.' % (cr.reading[:rl], handaku_r)
            s = Segment(SegmentTag.Handakuten, char, index, cr.reading, cr.id,
                        reading[:rl+ol], info)
            variants.append([handaku_r, s])
        
        if last_k == u'つ' or last_k == u'ツ':
            if len(r) > 1: #there may be a case like つ.む == つ
                soku_r = r[:-1] + tools.get_sokuon(r[-1])
                info = 'The last reading character, つ, became a っ (sokuon). '\
                        '%s became %s.' % (cr.reading[:rl], soku_r)
                s = Segment(SegmentTag.Sokuon, char, index, cr.reading, cr.id,
                            reading[:rl+ol], info)
                variants.append([soku_r, s])

        if o is not u'':
            oku_last_k = o[len(o)-1]
            if oku_last_k == u'つ':  # or last_k == u'ツ':                       
                soku_o = o[:-1] + u'っ'
                oku_info = 'つ became っ (sokuon).'\
                           'Okurigana %s became %s.' % (o, soku_o)
                s = SegmentOku(SegmentOkuTag.Sokuon, soku_o, oku_info)                     
                oku_variants.append([soku_o, s])
                
            if tools.is_u(oku_last_k):
                i_o = o[:-1] + tools.u_to_i(oku_last_k)
                oku_info = 'Inflected u-verb. Okurigana %s became %s.' % (o, i_o)
                s = SegmentOku(SegmentOkuTag.Inflected, i_o, oku_info)
                oku_variants.append([i_o, s])    
        
        #The portion of the known word we want to test for this character        
        known_r = reading[:rl]
        
        #The portion of the known word we want to test as okurigana
        known_oku = word[1:ol + 1]
        
        for var in variants:
            v = var[0]
            seg = var[1]
            (r, s, o) = v.partition(".")
            #If they're not both katakana, convert the non-katakatana
            #to hiragana so we can compare them.
            if not (tools.is_kata(r[0]) and tools.is_kata(known_r[0])):
                known_r = tools.kata_to_hira(known_r)
                r = tools.kata_to_hira(r) 
                
            #Okurigana branch (if it has any)
            if o is not u'':
                #Try standard okurigana   
                if r == known_r and o == known_oku:
                    base = copy.copy(segments)
                    base.append(seg)
                    index += rl+ol
                    solve_reading(word[ol+1:], reading[ol+rl:], index, base)
                
                #Try all okurigana variants
                for oku_var in oku_variants:
                    ov = oku_var[0]
                    oseg = oku_var[1]
                    if r == known_r and known_oku == ov:
                        base = copy.copy(segments)
                        #Attach okurigana segment to base segment
                        seg.oku_segment = oku_var
                        base.append(seg)
                        index += rl+ol
                        solve_reading(word[ol+1:], reading[ol+rl:], index, base)
            #No Okurigana branch
            else:
                #Branch for standard reading with no transformations.
                if known_r.startswith(r):
                    #This branch for regular words and readings.
                    base = copy.copy(segments)
                    base.append(seg)
                    index += 1
                    solve_reading(word[1:], reading[rl:],
                                           index, base)
                    
                    #"Trailing kana" branch, for words like 守り人 = もりびと
                    #The り is part of the reading for 守 but isn't okurigana.
                    if len(word) > 1:
                        part_kana = word[1]
                        if tools.is_kana(part_kana) and part_kana == reading[rl-1]:
                            #Change the segment's tag and info before saving it
                            seg.tag = SegmentTag.Kana_trail
                            seg.info = "Trailing kana %s is part of the reading"\
                            " and isn't Okurigana." % part_kana
                            base = copy.copy(segments)
                            base.append(seg)
                            #Increment by 1, not 2. We included the character above.
                            index += 1                                 
                            solve_reading(word[2:], reading[rl:],
                                                   index, base)

def solve_reading(word, reading, index=0, segments=None):
    if segments == None:
        segments = []

    if len(word) == 0:
        solutions.append(segments)
    elif len(reading) == 0: #exhausted reading but still part of word left
        return
    else:
        char = word[0]
        if tools.is_kana(char):
            solve_kana(char, word, reading, index, segments)
        else:
            solve_character(char, word, reading, index, segments)

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
#        if i == 20000:
#            break
        segments = get_readings(word.keb, word.reb)
        for seg in segments:
            #print 'seg == ' , seg.unit
            found_l.append({'word_id':word.id, 'found':True})
            segment_l.append({'word_id':word.id,
                              'reading_id':seg.reading_id,
                              'index':seg.index})
    print "Saving..."
    u = word_t.update().where(word_t.c['id']==
                              bindparam('word_id')).\
                              values(found=bindparam('found'))
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
                #print "New found word %s" % word.keb, word.reb
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
        print 'character[%s]' % s.character,
        print 'reading[%s]' % s.reading,
        print 'index[%s]' % s.index,
        print 'tag[%s]' % s.tag,
        print 'dic_reading[%s]' % s.dic_reading,
        print 'reading_id[%s]' % s.reading_id
        


                
if __name__ == "__main__":

#
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
#    testme(u"刈り入れ人", u"かりいれびと")
#    testme(u"日帰り", u"ひがえり")        
#    testme(u"アリドリ科", u"ありどりか")
#    testme(u"赤鷽", u"アカウソ")
#    testme(u"重立った", u"おもだった")
#    testme(u"刈り手", u"かりて")
#    testme(u"働き蟻", u"はたらきあり")
#    testme(u"往き交い", u"いきかい")    
    testme(u"積み卸し", u"つみおろし")
    testme(u"包み紙", u"つつみがみ")
    testme(u"守り人", u"もりびと")
    testme(u"糶り", u"せり")       
    testme(u"バージョン", u"バージョン")
    testme(u"シリアルＡＴＡ", u"シリアルエーティーエー")

    fill_solutions() 
    print_stats()

#    testme(u"空白デリミター", u"くウハくデリミター")       
#    dry_run()

#    testme(u"日本刀", u"にほんとう")
    
    
#    testme(u"全国津々浦々", u"ぜんこくつつうらうら")
#    testme(u"酒機嫌", u"ささきげん")




    #testme(u"四日市ぜんそく", u"よっかいちぜんそく")
#    testme(u"お腹", u"おなか")
#    testme(u"今日", u"きょう")
#    testme(u"疾く疾く", u"とくとく") #potential missing kanji reading?
#    testme(u"当り", u"あたり")

#    cProfile.run('fill_solutions()', 'pstats')
#    p = pstats.Stats('pstats')
#    p.sort_stats('time', 'cum').print_stats(.5)

#last attempt
#There are 157902 entries in JMdict. A solution has been found for 130622 of them. (82%)
