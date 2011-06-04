# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import time
import copy
from sqlalchemy import MetaData
from sqlalchemy.sql import select, and_, or_, bindparam

from tools import is_u, u_to_i, is_kana, is_kata, kata_to_hira, has_dakuten,\
                  get_dakuten, has_handakuten, get_handakuten, is_hira,\
                  hira_to_kata
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
    #A SegmentOku object with information on the reading's Okurigana
    oku_segment = None
    
    def __init__(self, tag, character, index, dic_reading, reading_id,
                 reading):
        self.tag = tag
        self.character = character
        self.index = index
        self.dic_reading = dic_reading
        self.reading_id = reading_id
        self.reading = reading

class SegmentOku:
    #A SegmentOkuTag denoting the type of transformation of the reading.
    tag = None
    #the reading of this segment as it appears in the word
    reading = None    
    
    def __init__(self, tag, reading):
        self.tag = tag
        self.reading = reading

class Tree:
    parent = None
    segment = None
    next_reading = None
    
    def __init__(self, parent, segment, next_reading=0):
        self.parent = parent
        self.segment = segment
        self.next_reading = next_reading
      
    def get_branch_as_list(self):       
        segments = [self.segment]
        p = self.parent
        while p.segment is not None:
            segments.append(p.segment)
            p = p.parent
        segments.reverse()
        return segments

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


def solve_reading(word, reading):
    root = Tree(None, None)
     
    w_length = len(word)
    #list to store lists of branches that are continued at that character index
    #extra slot at the end will store solutions
    branches_at =  [[] for w in range(w_length+1)]
    branches_at[0].append(root)
    usable_branches = 1
    for w_index, w_char in enumerate(word):

        #No solvable branches left. Terminate early
        if usable_branches == 0:
            break
        branches_here = branches_at[w_index]
        
        #if no branches are expected to start here, move on
        if len(branches_here) == 0:
            continue

        usable_branches -= len(branches_here)

        if is_kana(w_char):
            usable_branches += solve_kana(w_char, w_index, reading,
                                         branches_here, branches_at)
        else:        
            usable_branches += solve_character(word, w_index, reading,
                                              branches_here, branches_at)
    for l in branches_at[-1]:
        if l.next_reading == len(reading):
            solutions.append(l.get_branch_as_list())
    return solutions


def solve_kana(w_char, w_index, reading, branches, branches_at):
    n_new = 0
    for branch in branches:
        r_index = branch.next_reading
        if r_index >= len(reading):
            continue
        r_char = reading[r_index]
        if is_kata(w_char) and is_hira(r_char):
            r_char = hira_to_kata(r_char)
    
        if w_char == r_char:
            s = Segment(SegmentTag.Kana, w_char, w_index, w_char, 0, r_char)
            branch = Tree(branch, s, r_index+1)
            branches_at[w_index+1].append(branch)
            n_new += 1
    return n_new


def solve_character(g_word, w_index, g_reading, branches, branches_at):
    new_branches = 0
    w_char = g_word[w_index]

    s = select([reading_t.c['id'], reading_t.c['reading']],
               reading_t.c['character']==w_char)
    char_readings = conn.execute(s).fetchall()
    
    #TODO: Handle non-kanji and non-kana characters
    if char_readings == None:
        print "Shouldn't be here for now."
        return None
    
    for cr in char_readings:
        (r, s, o) = cr.reading.partition(".")
        rl = len(r)  #reading length (non-okurigana portion)
        ol = len(o)  #okurigana length
            
        variants = []
        oku_variants = []
    
        word = g_word[w_index:]

        variants.append((cr.reading[:rl], SegmentTag.Regular))

        first_k = r[0]
        last_k = r[-1]

        if has_dakuten(first_k):
            d = get_dakuten(first_k)
            daku_r = d + cr.reading[1:rl]
            variants.append((daku_r, SegmentTag.Dakuten))
                               
        if has_handakuten(first_k):
            d = get_handakuten(first_k)
            handaku_r = d + cr.reading[1:rl]
            variants.append((handaku_r, SegmentTag.Handakuten))
        
        if last_k == u'つ' or last_k == u'ツ':
            if len(r) > 1: #there may be a case like つ.む == つ
                soku_r = r[:-1] + unichr(ord(r[-1])-1)
                variants.append((soku_r, SegmentTag.Sokuon))

        if o is not u'':
            #we're assuming okurigana is always hiragana
            #if it's ever changed, make sure the reading is grabbed from
            #reading, not o, to keep the original characters
            oku_variants.append((o, SegmentOkuTag.Regular))
            
            oku_last_k = o[len(o)-1]
            if oku_last_k == u'つ':                        
                soku_o = o[:-1] + u'っ'
                oku_variants.append((soku_o, SegmentOkuTag.Sokuon))
                
            if is_u(oku_last_k):
                i_o = o[:-1] + u_to_i(oku_last_k)
                oku_variants.append((i_o, SegmentOkuTag.Inflected))    

        #The portion of the known word we want to test as okurigana
        known_oku = word[1:ol+1]

        for branch in branches:
            r_index = branch.next_reading
            if r_index >= len(g_reading):
                continue
            
            reading = g_reading[r_index:]
            
            #The portion of the known word we want to test for this character        
            known_r = reading[:rl]
            kr_is_kata = is_kata(known_r[0])

            for var in variants:
                (r, tag) = var
                                
                #If they're not both katakana, convert the non-katakana
                #to hiragana so we can compare them.
                if kr_is_kata and not is_kata(r[0]):
                    known_r = kata_to_hira(known_r)
                elif not kr_is_kata and is_kata(r[0]):
                    r = kata_to_hira(r)
                     
                #Okurigana branch (if it has any)
                if o is not u'':                       
                    #Try all okurigana variants
                    for oku_var in oku_variants:                       
                        (ov, otag) = oku_var
                        if r == known_r and known_oku == ov:
                            #Attach okurigana segment to base segment
                            seg = Segment(tag, w_char, w_index, cr.reading,
                                          cr.id, reading[:rl+ol])
                            oseg = SegmentOku(otag, ov)
                            seg.oku_segment = oseg
                            n_branch = Tree(branch, seg, r_index+rl+ol)
                            branches_at[w_index+1+ol].append(n_branch)
                            new_branches += 1
    
                #No Okurigana branch
                else:
                    #Branch for standard reading with no transformations.
                    if known_r.startswith(r):
                        #This branch for regular words and readings.
                        seg = Segment(tag, w_char, w_index, cr.reading, cr.id,
                        reading[:rl+ol])
            
                        n_branch = Tree(branch, seg, r_index+rl)
                        branches_at[w_index+1].append(n_branch)
                        new_branches += 1
                        
                        #"Trailing kana" branch, for words like 守り人 = もりびと
                        #The り is part of the reading for 守 but isn't okurigana.
                        if len(word) > 1:
                            part_kana = word[1]
                            if (is_kana(part_kana) and
                                part_kana == reading[rl-1]):
                                seg = Segment(SegmentTag.Kana_trail, w_char,
                                              w_index, cr.reading, cr.id,
                                reading[:rl+ol])

                                n_branch = Tree(branch, seg, r_index+rl)
                                branches_at[w_index+2].append(n_branch)
                                new_branches += 1
    return new_branches    
            

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
    start = time.time()
    conn.execute(segment_t.delete())
    s = select([word_t])
    words = conn.execute(s).fetchall()
    goal = len(words)
    save_now = 0
    total = 0
    i = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        for seg in segments:
            #print 'seg == ' , seg.unit
            found_l.append({'word_id':word.id, 'found':True})
            segment_l.append({'word_id':word.id,
                              'reading_id':seg.reading_id,
                              'index':seg.index})
#        i += 1
#        if i > 10000:
#            return
        save_now += 1
        if save_now > 20000:
            save_now = 0
            save_found()
            total += 20000
            print "Progress %s %% in %s seconds" % ((float(total) / goal)*100,
                                                    (time.time() - start))
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
                print "New found word %s" % word.keb, word.reb
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
        if s.oku_segment is not None:
            print 'oku_reading[%s]' % s.oku_segment.reading
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
#    testme(u"自動金銭出入機", u"じどうきんせんしゅつにゅうき")    

    fill_solutions() 
#    print_stats()     
#    dry_run()


#    testme(u"全国津々浦々", u"ぜんこくつつうらうら")
#   testme(u"酒機嫌", u"ささきげん")
#    testme(u"四日市ぜんそく", u"よっかいちぜんそく")
#    testme(u"お腹", u"おなか")
#    testme(u"今日", u"きょう")
#    testme(u"当り", u"あたり")

#There are 159203 entries in JMdict. A solution has been found for 131418 of them. (82%)
