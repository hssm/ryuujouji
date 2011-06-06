# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt


from sqlalchemy import MetaData
from sqlalchemy.sql import select, bindparam

from tools import is_u, u_to_i, is_kana, is_kata, kata_to_hira, has_dakuten,\
                  get_dakuten, has_handakuten, get_handakuten, is_hira,\
                  hira_to_kata
import db

conn = db.get_connection()
meta = MetaData()
meta.bind = conn.engine
meta.reflect()
reading_t = meta.tables['reading']

r_select = select([reading_t.c.id, reading_t.c.reading]).\
                  where(reading_t.c.character==bindparam('character'))

class SegmentTag:
    """Enums for types of transformations of readings."""
    (Kana, Regular, Dakuten, Handakuten, Sokuon, Kana_trail, OkuRegular,
    OkuSokuon, OkuInflected)  = range(9)

class Segment:
    """Class to hold segment information."""
    #A list of SegmentTags denoting the types of transformations of the reading.
    tags = None
    #The character we are solving
    character = None
    #The nth kanji in the word
    nth_kanji = None
    #Like nth_kanji, but nth from the right
    nth_kanjir = None
    #The dictionary reading of the character
    dic_reading = None
    #The database ID of the reading used to solve this segment
    reading_id = None
    #The reading of this segment as it appears in the word
    reading = None
    #The reading of this segment's okurigana as it appears in the word
    oku_reading = None
    
    def __init__(self, tag, character, dic_reading, reading_id, reading):
        self.tags = [tag]
        self.character = character
        self.dic_reading = dic_reading
        self.reading_id = reading_id
        self.reading = reading
    
class Tree:
    parent = None
    segment = None
    #The index in the reading that the next segment starts at
    next_reading = 0
    #Keep track of number of kanji in the branch (to figure out indexes later)
    k_in_branch = -1
    is_kana = False
    
    def __init__(self, parent, segment):
        #If not root
        if segment is not None:
            #Calculate the next reading index for this branch
            self.next_reading = parent.next_reading + len(segment.reading)

            #Increment kanji index if it's a kanji. Also, add to k_in_branch
            #which we use later to calculate the reverse index.
            if not segment.tags[0] == SegmentTag.Kana:
                self.k_in_branch = parent.k_in_branch + 1
                segment.nth_kanji = self.k_in_branch
            else:
                self.is_kana = True
                self.k_in_branch = parent.k_in_branch
                segment.nth_kanji = None

        self.parent = parent
        self.segment = segment
        
         
    def get_branch_as_list(self):
        #Here's a good place to add the reverse kanji index since 
        #we're iterating backwards already.
        indexr = 0
        segments = []
        p = self
        while p.segment is not None:
            if p.segment.tags[0] is not SegmentTag.Kana:
                p.segment.nth_kanjir = indexr
                indexr += 1
            else:
                p.segment.nth_kanjir = None
            segments.append(p.segment)
            p = p.parent
        segments.reverse()
        return segments


def get_readings(word, reading):
    """Returns a list of dictionaries separating the word into portions of
    character-reading pairs that form the word."""
    
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
    solutions = []
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
            s = Segment(SegmentTag.Kana, w_char, w_char, 0, r_char)
            n_branch = Tree(branch, s)
            branches_at[w_index+1].append(n_branch)
            n_new += 1
    return n_new


def solve_character(g_word, w_index, g_reading, branches, branches_at):
    new_branches = 0
    w_char = g_word[w_index]

    char_readings = conn.execute(r_select, character=w_char).fetchall() 
    
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
            oku_variants.append((o, SegmentTag.OkuRegular))
            
            oku_last_k = o[len(o)-1]
            if oku_last_k == u'つ':                        
                soku_o = o[:-1] + u'っ'
                oku_variants.append((soku_o, SegmentTag.OkuSokuon))
                
            if is_u(oku_last_k):
                i_o = o[:-1] + u_to_i(oku_last_k)
                oku_variants.append((i_o, SegmentTag.OkuInflected))    

        #The portion of the known word we want to test as okurigana
        known_oku = word[1:ol+1]
        
        for b in branches:
            r_index = b.next_reading
            if r_index >= len(g_reading):
                continue
            
            reading = g_reading[r_index:]
            
            #The portion of the known word we want to test for this character        
            known_r = reading[:rl]
            #The portion of the known reading we want to test as okurigana
            known_oku_r = reading[rl:rl+ol]
            
            kr_is_kata = is_kata(known_r[0])

            for (r, tag) in variants:
                #If they're not both katakana, convert the non-katakana
                #to hiragana so we can compare them.
                if kr_is_kata and not is_kata(r[0]):
                    known_r = kata_to_hira(known_r)
                elif not kr_is_kata and is_kata(r[0]):
                    r = kata_to_hira(r)
                     
                #Okurigana branch (if it has any)
                if o is not u'':                       
                    #Try all okurigana variants
                    for (ov, otag) in oku_variants:
                        #Check for matches in the word
                        if r == known_r and known_oku == ov:
                            if is_kata(known_oku_r) and not is_kata(ov):
                                ov = hira_to_kata(ov)
                            #ALSO check for matches in the reading
                            if ov == known_oku_r:
                                seg = Segment(tag, w_char, cr.reading, cr.id,
                                              reading[:rl]+word[1:1+ol])
                                seg.oku_reading = ov 
                                seg.tags.append(otag)
                                n_branch = Tree(b, seg)
                                branches_at[w_index+1+ol].append(n_branch)
                                new_branches += 1
    
                #No Okurigana branch
                else:
                    #Branch for standard reading with no transformations.
                    if known_r.startswith(r):
                        #This branch for regular words and readings.
                        seg = Segment(tag, w_char, cr.reading, cr.id,
                                      reading[:rl+ol])
            
                        n_branch = Tree(b, seg)
                        branches_at[w_index+1].append(n_branch)
                        new_branches += 1
                        
                        #"Trailing kana" branch, for words like 守り人 = もりびと
                        #The り is part of the reading for 守 but isn't okurigana.
                        if len(word) > 1:
                            part_kana = word[1]
                            if (is_kana(part_kana) and
                                part_kana == reading[rl-1]):
                                seg = Segment(SegmentTag.Kana_trail, w_char,
                                              cr.reading, cr.id,
                                reading[:rl+ol])

                                n_branch = Tree(b, seg)
                                branches_at[w_index+2].append(n_branch)
                                new_branches += 1
    return new_branches    
