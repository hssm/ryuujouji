# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import cProfile
import pstats
import time
import copy
from sqlalchemy import MetaData
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

conn = db.get_connection()

meta = MetaData()
meta.bind = conn.engine
meta.reflect()
reading_t = meta.tables['reading']
word_t = meta.tables['word']
segment_t = meta.tables['segment']

solutions = []
segments = []
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


class Tree:
    parent = None
    segment = None
    next_word = None
    next_reading = None
    
    def __init__(self, parent, segment, next_word=0, next_reading=0):
        self.parent = parent
        self.segment = segment
        self.next_word = next_word
        self.next_reading = next_reading
        
    def get_branch_as_list(self):
        segments = [self.segment]
        p = self.parent
        while p is not None:
            segments.append(p.segment)
            p = p.parent
        
        segments.reverse()
        return segments

def solve_reading(word, reading, index=0):

    leaves = []
    next_leaves = []

    for i, char in enumerate(word):
        char = word[i]

        leaves = next_leaves
        next_leaves = []    
        
        if i == 0:
            if tools.is_kana(char):
                solve_kana(word, reading, None, next_leaves)                  
            else:
                solve_character(word, reading, None, next_leaves)
        else:    
            for l in leaves:
                if i == l.next_word:                        
                    if tools.is_kana(char):
                        solve_kana(word, reading, l, next_leaves)                  
                    else:
                        solve_character(word, reading, l, next_leaves)
                else:
                    next_leaves.append(l)
                        
                    
    for l in next_leaves:
        if l.next_word == len(word) and l.next_reading == len(reading):
            solutions.append(l.get_branch_as_list())           

    return solutions

def solve_kana(word, reading, leaf, next_leaves):
    if leaf is None:
        word_index = 0
        reading_index = 0
    else:
        word_index = leaf.next_word
        reading_index= leaf.next_reading

    if reading_index >= len(reading):
        return
    
    w_char = word[word_index]
    r_char = reading[reading_index]
 
    if tools.is_kata(w_char) and tools.is_hira(r_char):
        r_char = tools.hira_to_kata(r_char)

    if w_char == r_char:
        s = Segment(SegmentTag.Kana, w_char, word_index, w_char, 0,
                    reading[reading_index], 'Kana')
        branch = Tree(leaf, s, word_index+1, reading_index+1)
        next_leaves.append(branch)

z = 0
yy = 0
def solve_character(word, reading, leaf, next_leaves):
    global z
    global yy
    xx = time.time()
    if leaf is None:
        word_index = 0
        reading_index = 0
    else:
        word_index = leaf.next_word
        reading_index= leaf.next_reading
    
    if reading_index >= len(reading):
        return
    
    w_char = word[word_index]
    
    word = word[word_index:]
    reading = reading[reading_index:]
    
    
    s = select([reading_t.c['id'], reading_t.c['reading']],
               reading_t.c['character']==w_char)
    
    x = time.time()
    char_readings = conn.execute(s).fetchall()
    z += time.time() - x
    
    #TODO: Handle non-kanji and non-kana characters
    if char_readings == None:
        print "Shouldn't be here for now."
        return None

    for cr in char_readings:
        #print w_char, '=', cr.reading
        variants = []
        oku_variants = []
       
        (r, s, o) = cr.reading.partition(".")
        rl = len(r)  #reading length (non-okurigana portion)
        ol = len(o)  #okurigana length

        s = Segment(SegmentTag.Regular, w_char, word_index, cr.reading, cr.id,
                    reading[:rl+ol],
                    'Regular character reading: '+cr.reading[:rl])
        variants.append([cr.reading, s])
        
        first_k = r[0]
        last_k = r[-1]
        
        if tools.has_dakuten(first_k):
            d = tools.get_dakuten(first_k)
            daku_r = d + cr.reading[1:]
            info = 'Dakuten (゛) added to first syllable in reading. '\
                    '%s became %s.' % (cr.reading[:rl], daku_r)
            s = Segment(SegmentTag.Dakuten, w_char, word_index, cr.reading,
                        cr.id, reading[:rl+ol], info)
            variants.append([daku_r, s])
                               
        if tools.has_handakuten(first_k):
            d = tools.get_handakuten(first_k)
            handaku_r = d + cr.reading[1:]
            info = 'Handakuten (゜) added to first syllable in reading. '\
                    '%s became %s.' % (cr.reading[:rl], handaku_r)
            s = Segment(SegmentTag.Handakuten, w_char, word_index, cr.reading,
                        cr.id, reading[:rl+ol], info)
            variants.append([handaku_r, s])
        
        if last_k == u'つ' or last_k == u'ツ':
            if len(r) > 1: #there may be a case like つ.む == つ
                soku_r = r[:-1] + tools.get_sokuon(r[-1])
                info = 'The last character, つ, became a っ (sokuon). '\
                        '%s became %s.' % (cr.reading[:rl], soku_r)
                s = Segment(SegmentTag.Sokuon, w_char, word_index, cr.reading,
                            cr.id, reading[:rl+ol], info)
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
                oku_info = ('Inflected u-verb. Okurigana %s became %s.' %
                            (o, i_o))
                s = SegmentOku(SegmentOkuTag.Inflected, i_o, oku_info)
                oku_variants.append([i_o, s])    
        
        #The portion of the known word we want to test for this character        
        known_r = reading[:rl]
        
        #The portion of the known word we want to test as okurigana
        known_oku = word[1:ol+1]
        
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
                #TODO: move regular okurigana part to variant appending at the top
                #Try standard okurigana   
                if r == known_r and o == known_oku:
                    os = SegmentOku(SegmentOkuTag.Regular, o,
                                    'Regular Okurigana: %s' % o )
                    seg.oku_segment = os
                    branch = Tree(leaf, seg, word_index+1+ol, reading_index+rl+ol)
                    next_leaves.append(branch)
                    
                #Try all okurigana variants
                for oku_var in oku_variants:
                    ov = oku_var[0]
                    oseg = oku_var[1]
                    if r == known_r and known_oku == ov:
                        #Attach okurigana segment to base segment
                        seg.oku_segment = oseg
                        branch = Tree(leaf, seg, word_index+1+ol, reading_index+rl+ol)
                        next_leaves.append(branch)

            #No Okurigana branch
            else:
                #Branch for standard reading with no transformations.
                if known_r.startswith(r):
                    #This branch for regular words and readings.
                    branch = Tree(leaf, seg, word_index+1, reading_index+rl)
                    next_leaves.append(branch)

                    #"Trailing kana" branch, for words like 守り人 = もりびと
                    #The り is part of the reading for 守 but isn't okurigana.
                    if len(word) > 1:
                        part_kana = word[1]
                        if (tools.is_kana(part_kana) and
                            part_kana == reading[rl-1]):
                            #Change the segment's tag and info before saving it
                            seg.tag = SegmentTag.Kana_trail
                            seg.info = ("Trailing kana %s is part of the "
                            "reading and isn't Okurigana." % part_kana)
                            branch = Tree(leaf, seg, word_index+2, reading_index+rl)
                            next_leaves.append(branch)
                            
    yy += time.time() - xx                     

found_l = []
segment_l = []

def save_found():
    global found_l
    global segment_l
    
    u = word_t.update().where(word_t.c['id']==
                              bindparam('word_id')).\
                              values(found=bindparam('found'))
    conn.execute(u, found_l)
    conn.execute(segment_t.insert(), segment_l)
    found_l = []    
    segment_l = []
    
def fill_solutions():
    global z
    global yy
    start = time.time()
    conn.execute(segment_t.delete())
    s = select([word_t])
    words = conn.execute(s).fetchall()
    goal = len(words)
    save_now = 0
    total = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        for seg in segments:
            #print 'seg == ' , seg.unit
            found_l.append({'word_id':word.id, 'found':True})
            segment_l.append({'word_id':word.id,
                              'reading_id':seg.reading_id,
                              'index':seg.index})
        save_now += 1
        if save_now > 5000:
            save_now = 0
            save_found()
            total += 5000
            print "Progress %s %% in %s seconds" % ((float(total) / goal)*100,
                                                    (time.time() - start))
            print 'z took ', z
            print 'yy took ', yy
            z = 0
            yy = 0

    save_found()
    

    print 'took %s seconds' % (time.time() - start)

def dry_run():
    """Don't save any changes to the database, but check if the present
     parsing behaviour breaks the solving of an already-solved entry.
     """
     
    start = time.time()
    conn.execute(segment_t.delete())
    s = select([word_t])
    words = conn.execute(s)
    newly_solved = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        if word.found == True:
            if len(segments) == 0:
                print "Regression for word %s == %s" %(word.keb, word.reb)
        else:
            if len(segments) > 0:
                newly_solved += 1
                #print "New found word %s" % word.keb, word.reb
    print "The changes will solve another %s entries. " % newly_solved


def print_stats():
    s = select([word_t])
    words = conn.execute(s).fetchall()
    n = len(words)
    
    s = select([word_t], word_t.c['found'] == True)
    found = conn.execute(s).fetchall()
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
        print 'reading_id[%s]' % s.reading_id,
        print 'info[%s]' % s.info,
        if s.oku_segment is not None:
            print 'oku_reading[%s]' % s.oku_segment.reading,
            print 'oku_info[%s]' % s.oku_segment.info
        else:
            print
                        
if __name__ == "__main__":
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
#    testme(u"積み卸し", u"つみおろし")
#    testme(u"包み紙", u"つつみがみ")
#    testme(u"守り人", u"もりびと")
#    testme(u"糶り", u"せり")       
#    testme(u"バージョン", u"バージョン")
#    testme(u"シリアルＡＴＡ", u"シリアルエーティーエー")
#    testme(u"猶太", u"ユダヤ")
    

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
#There are 159203 entries in JMdict. A solution has been found for 131418 of them. (82%)
#There are 157902 entries in JMdict. A solution has been found for 130442 of them. (82%)