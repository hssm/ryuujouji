# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt


from sqlalchemy.sql import select, bindparam

from tools import is_u, u_to_i, is_kana, is_kata, kata_to_hira, has_dakuten,\
                  get_dakuten, has_handakuten, get_handakuten, is_hira,\
                  hira_to_kata
import reading_db
from segments import SegmentTag, Segment

conn = reading_db.get_connection()
reading_t = reading_db.reading_t

r_select = select([reading_t.c.id, reading_t.c.reading, reading_t.c.okurigana]).\
                  where(reading_t.c.character==bindparam('character'))
 
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
            if segment.is_kanji:
                self.k_in_branch = parent.k_in_branch + 1
                segment.index = self.k_in_branch
            else:
                self.is_kana = True
                self.k_in_branch = parent.k_in_branch
                segment.index = None

        self.parent = parent
        self.segment = segment
         
    def get_branch_as_list(self):
        #Here's a good place to add the reverse kanji index since 
        #we're iterating backwards already.
        indexr = 0
        segments = []
        p = self
        while p.segment is not None:
            if p.segment.is_kanji:
                p.segment.indexr = indexr
                indexr += 1
            else:
                p.segment.indexr = None
            segments.append(p.segment)
            p = p.parent
        segments.reverse()
        return segments


def solve_reading(word, reading):
    """Returns a list of dictionaries separating the word into portions of
    character-reading pairs that form the word."""
        
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
    
    if len(solutions) > 0:
        return min(solutions, key=len)
    else:
        return []


def solve_kana(w_char, w_index, reading, branches, branches_at):
    n_new = 0
    for branch in branches:
        r_index = branch.next_reading
        if r_index >= len(reading):
            continue
        r_char = reading[r_index]
        if is_kata(w_char) and is_hira(r_char):
            r_char = hira_to_kata(r_char)
        if is_hira(w_char) and is_kata(r_char):
            r_char = kata_to_hira(r_char) 
    
        if w_char == r_char:
            s = Segment(None, w_char, w_char, 0, reading[r_index])
            n_branch = Tree(branch, s)
            branches_at[w_index+1].append(n_branch)
            n_new += 1
    return n_new


def solve_character(g_word, w_index, g_reading, branches, branches_at):
    new_branches = 0
    w_char = g_word[w_index]

    #replace 々 with its respective kanji
    if w_char == u'々' and w_index > 0:
        q_char = g_word[w_index-1]
    else:
        q_char = w_char

    char_readings = conn.execute(r_select, character=q_char).fetchall() 
    
    #TODO: Handle non-kanji and non-kana characters
    if char_readings == None:
        print "Shouldn't be here for now."
        return None
            
    for cr in char_readings:
        r = cr.reading
        o = cr.okurigana
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
            #The readings from kanjidic always have hiragana okurigana
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
                        
                        #Note: okurigana in the word is always hiragana.
                        #However, the reading might still have it as katakana.
                        #If it is, convert the oku variant to katakana also
                        #so we can compare them.
                        if r == known_r and known_oku == ov:
                            if is_kata(known_oku_r) and not is_kata(ov):
                                ov = hira_to_kata(ov)
                            #ALSO check for matches in the reading
                            if ov == known_oku_r:
                                seg = Segment(tag, w_char, cr.reading, cr.id,
                                              reading[:rl+ol])
                                seg.append_oku(ov, o) 
                                seg.tags.append(otag)
                                n_branch = Tree(b, seg)
                                branches_at[w_index+1+ol].append(n_branch)
                                new_branches += 1
    
                #No Okurigana branch
                else:
                    #Branch for standard reading with no transformations.
                    if known_r.startswith(r):
                        #This branch for regular words and readings.
                        seg = Segment(tag, w_char, cr.reading, cr.id, reading[:rl+ol])
                        n_branch = Tree(b, seg)
                        branches_at[w_index+1].append(n_branch)
                        new_branches += 1
                        
                        #"Trailing kana" branch, for words like 守り人 = もりびと
                        #The り is part of the reading for 守 but isn't okurigana.
                        if len(word) > 1:
                            w_trail = word[1]
                            r_trail = reading[rl-1]
                            if is_kata(r_trail) and not is_kata(w_trail):
                                w_trail = hira_to_kata(w_trail)
                                
                            if (is_kana(w_trail) and w_trail == r_trail):
                                seg = Segment(SegmentTag.KanaTrail, w_char,
                                              cr.reading, cr.id, reading[:rl+ol])
                                n_branch = Tree(b, seg)
                                branches_at[w_index+2].append(n_branch)
                                new_branches += 1
    return new_branches    


def test_print(k, r):
    print
    print "Solving: %s == %s" % (k, r)
    segments = solve_reading(k, r)

    for s in segments:
        print 'character[%s]' % s.character,
        print 'reading[%s]' % s.reading,
        print 'index[%s]' % s.index,
        print 'indexr[%s]' % s.indexr,
        print 'tags%s' % s.tags,
        print 'dic_reading[%s]' % s.dic_reading,
        print 'reading_id[%s]' % s.reading_id,
        print

if __name__ == "__main__":
#    test_print(u'漢字', u'かんじ')
#    test_print(u"小牛", u"こうし")
#    test_print(u"バス停", u"バスてい")
#    test_print(u"非常事態", u"ひじょうじたい")
#    test_print(u"建て替える", u"たてかえる")
#    test_print(u"小さい", u"ちいさい")
#    test_print(u"鉄道公安官", u"てつどうこうあんかん")
#    test_print(u"手紙", u"てがみ")
#    test_print(u"筆箱", u"ふでばこ")
#    test_print(u"人人", u"ひとびと")
#    test_print(u"岸壁", u"がんぺき")
#    test_print(u"一つ", u"ひとつ")
#    test_print(u"別荘", u"べっそう")
#    test_print(u"出席", u"しゅっせき")
#    test_print(u"結婚", u"けっこん")
#    test_print(u"分別", u"ふんべつ")   
#    test_print(u"刈り入れ人", u"かりいれびと")
#    test_print(u"日帰り", u"ひがえり")        
#    test_print(u"アリドリ科", u"ありどりか")
#    test_print(u"赤鷽", u"アカウソ")
#    test_print(u"重立った", u"おもだった")
#    test_print(u"刈り手", u"かりて")
#    test_print(u"働き蟻", u"はたらきあり")
#    test_print(u"往き交い", u"いきかい")    
#    test_print(u"積み卸し", u"つみおろし")
#    test_print(u"包み紙", u"つつみがみ")
#    test_print(u"守り人", u"もりびと")
#    test_print(u"糶り", u"せり")       
#    test_print(u"バージョン", u"バージョン")
#    test_print(u"シリアルＡＴＡ", u"シリアルエーティーエー")
#    test_print(u"自動金銭出入機", u"じどうきんせんしゅつにゅうき")
    test_print(u"全国津々浦々", u"ぜんこくつつうらうら")
#    test_print(u"作り茸", u"ツクリタケ")     
#    test_print(u"別荘", u"ベッソウ")
#    test_print(u"守り人", u"モリビト")
#    test_print(u"建て替える", u"タテカエル")
#    test_print(u"一つ", u"ヒトツ")
#    
#    test_print(u'先程',u'サキホド')
#    test_print(u'先程',u'さきほど')
#    
#    test_print(u'先週',u'センシュウ')
#    test_print(u'先週',u'せんしゅう')
#
#    test_print(u'姉さん',u'ネエサン')
#    test_print(u'姉さん',u'ねえさん')
#
#    test_print(u'近寄る',u'チカヨル')
#    test_print(u'近寄る',u'ちかよる')
#
#    test_print(u'弱気',u'ヨワキ')
#    test_print(u'弱気',u'よわき')
##    
#    test_print(u'あの',u'アノ')
#    test_print(u'アノ',u'あの')
    
#    
#    test_print(u'馬を水辺に導く事は出来るが馬に水を飲ませる事は出来ない',
#               u'うまをみずべにみちびくことはできるがうまにみずをのませることはできない')
