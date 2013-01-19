# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import sqlite3
from tools import is_kana, is_kata, kata_to_hira, is_hira, hira_to_kata

from variants import get_variants, get_oku_variants
from segments import SegmentTag, Segment
from paths import READINGS_PATH
from branch import Branch

conn = sqlite3.connect(READINGS_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()


def solve(word, reading):
    s = Solver(word, reading)
    return s.solution
    
def getSolver(word, reading):
    """ Return a solver object (still holding state information, including
    other solutions, if there were any)."""
    s = Solver(word, reading)
    return s
    
def print_segments(word, reading):
    print "%s[%s]" % (word, reading)
    s = Solver(word, reading)
    segments = s.solution

    if segments is None:
        print 'unknown'
    else:
        for s in segments:
            print "%s %s" % (s.grapheme, s.reading)

def print_segments_to_file(word, reading, out):
    out.write("%s[%s]\n" % (word, reading))
    s = Solver(word, reading)
    segments = s.solution

    if segments is None:
        out.write('unknown\n')
    else:
        for s in segments:
            out.write("%s %s\n" % (s.grapheme, s.reading))

def print_verbose(word, reading):
    print "%s[%s]" % (word, reading)
    s = Solver(word, reading)
    segments = s.solution

    if segments is None:
        print 'unknown'
    else:
        for s in segments:
            print 'grapheme[%s]' % s.grapheme,
            print 'character[%s]' % s.character,
            print 'reading[%s]' % s.reading,
            print 'index[%s]' % s.index,
            print 'indexr[%s]' % s.indexr,
            print 'tags%s' % s.tags,
            print 'dic_reading[%s]' % s.dic_reading,
            print 'reading_id[%s]' % s.reading_id,
            print
    print
            
def print_all_verbose(word, reading):
    print "%s[%s]" % (word, reading)
    s = Solver(word, reading)
    for sol in s.solutions:
        if sol is None:
            print 'unknown'
        else:
            print "Solution #"
            for s in sol:
                print 'grapheme[%s]' % s.grapheme,
                print 'character[%s]' % s.character,
                print 'reading[%s]' % s.reading,
                print 'index[%s]' % s.index,
                print 'indexr[%s]' % s.indexr,
                print 'tags%s' % s.tags,
                print 'dic_reading[%s]' % s.dic_reading,
                print 'reading_id[%s]' % s.reading_id,
                print
        print


class Solver:
    
    def __init__(self, word, reading):
        self.word = word
        self.reading = reading
        
        #The index of the character in the grapheme we are stepping through
        self.__w_index = 0 #TODO: rename to g_index to reflect purpose

        #The character in the grapheme we are stepping through
        self.__w_char = word[self.__w_index]

        #The branches that begin at the character index in the grapheme.
        #At each index of __branches_at that matches the grapheme, a list is stored
        #containing the branches to continue solving. The size of __branches_at is
        #len(word) + 1, with the extra slot at the end holding the branches that
        #have successfully reached the end (AKA solutions).
        self.__branches_at = []

        #The branches at __branches_at[__w_index]
        self.__current_branches = None #TODO: rename this as well.
        
        #If this drops to 0, we can't build a solution anymore, so quit early
        self.__usable_branches = 1
        
        #Holds all solutions found. A solution is a list of Segment objects.
        #The Segments will be ordered as they appear in the word.
        self.solutions = []
        
        #The highest ranked solution
        self.solution = None
        
        self.__solve_reading(word, reading)

    def get_solution(self):
        return self.solution

    def get_all_solutions(self):
        return self.solutions
    
    def __solve_reading(self, word, reading):
        """Returns a list of dictionaries separating the word into portions of
        character-reading pairs that form the word."""
            
        root = Branch(None, None)
        w_length = len(self.word)
        
        #list to store lists of branches that are continued at that character index
        #extra slot at the end will store solutions
        self.__branches_at =  [[] for w in range(w_length+1)]
        self.__branches_at[0].append(root)

        for (w_index, w_char) in enumerate(self.word):
    
            self.__w_char = w_char
            self.__w_index = w_index
            
            #No solvable branches left. Terminate early
            if self.__usable_branches == 0:
                break

            self.__current_branches = self.__branches_at[w_index]
            
            #if no branches are expected to start here, move on
            if len(self.__current_branches) == 0:
                continue
    
            #We are going to continue with the branches at this location,
            #so consider them no longer usable (since they have been used)
            self.__usable_branches -= len(self.__current_branches)
    
            if is_kana(w_char):
                self.__solve_kana()
            else:        
                self.__solve_character()
        
        #For all solutions (branches that made it to the end)        
        for seg_list in self.__branches_at[-1]:
            #While we may have found a portion of the reading that belongs to
            #each character, make sure there aren't any "dangling" characters
            #at the end of the reading that haven't been matched
            if seg_list.next_reading == len(self.reading):
                self.solutions.append(seg_list.get_branch_as_list())
        
        #TODO: need a better ranking system than just the shortest solution.
        if len(self.solutions) > 0:
            self.solution = min(self.solutions, key=len)

    
    def __solve_kana(self):

        for branch in self.__current_branches:
            #The next character in the reading that this branch starts at
            r_index = branch.next_reading
            
            if r_index >= len(self.reading):
                continue
            
            r_char = self.reading[r_index]
            if is_kata(self.__w_char) and is_hira(r_char):
                r_char = hira_to_kata(r_char)
            if is_hira(self.__w_char) and is_kata(r_char):
                r_char = kata_to_hira(r_char) 
        
            if self.__w_char == r_char:
                s = Segment(None, self.__w_char, self.__w_char, 0,
                            self.reading[r_index], self.__w_char)
                n_branch = Branch(branch, s)
                self.__branches_at[self.__w_index+1].append(n_branch)
                self.__usable_branches += 1

    def __solve_character(self):
    
        #replace 々 with its respective kanji
        if self.__w_char == u'々' and self.__w_index > 0:
            q_char = self.word[self.__w_index-1]
        else:
            q_char = self.__w_char
    
        s = "select id, reading from reading where character=?"
        char_readings = c.execute(s, q_char).fetchall()
                
        for cr in char_readings:
            dic_r = cr['reading']
                              
            word = self.word[self.__w_index:]
            word_len = len(word) #so we don't check ahead of it
    
            variants = get_variants(dic_r)
            
#            print "-----" + cr['reading'] + "-----"
#            for (r, tag, rl) in variants:
#                print r, tag

            for b in self.__current_branches:
                r_index = b.next_reading
                if r_index >= len(self.reading):
                    continue
                
                reading = self.reading[r_index:]
                
                for var in variants:
                    r = var.reading
                    tags = var.tags
                    rl = var.length
                    
                    known_r = reading[:rl]
                    kr_is_kata = is_kata(known_r[0])
                    
                    #If they're not both katakana, convert the non-katakana
                    #to hiragana so we can compare them.
                    if kr_is_kata and not is_kata(r[0]):
                        known_r = kata_to_hira(known_r)
                    elif not kr_is_kata and is_kata(r[0]):
                        r = kata_to_hira(r)
                                       
                    #we want a complete match of reading to kanji reading variant
                    match_length = 0
                    
                    #trailing kana (after kanji) in the word that is part of the reading
                    w_trail = 0 
                    for (i, j) in zip(known_r, r):
                        if i == j:
                            match_length += 1
                            #also check ahead for kana in the word that could
                            #belong to this reading
                            if w_trail+1 < word_len and word[w_trail + 1] == i:
                                w_trail += 1
                    
                    if match_length == len(r):
                        seg = Segment(tags, self.__w_char, dic_r, cr['id'],
                                      reading[:rl], word[:1])
                        n_branch = Branch(b, seg)
                        self.__branches_at[self.__w_index+1].append(n_branch)
                        self.__usable_branches += 1
                        
                        if w_trail > 0:
                            seg = Segment(tags, self.__w_char,
                                          dic_r, cr['id'], reading[:rl],
                                          word[:1+w_trail])
                            n_branch = Branch(b, seg)
                            self.__branches_at[self.__w_index+1+w_trail].append(n_branch)
                            self.__usable_branches += 1  


if __name__ == "__main__":

#    print_verbose(u'漢字', u'かんじ')
#    print_verbose(u"小牛", u"こうし")
#    print_verbose(u"バス停", u"バスてい")
#    print_verbose(u"非常事態", u"ひじょうじたい")
#    print_verbose(u"建て替える", u"たてかえる")
#    print_verbose(u"小さい", u"ちいさい")
#    print_verbose(u"鉄道公安官", u"てつどうこうあんかん")
#    print_verbose(u"手紙", u"てがみ")
#    print_verbose(u"筆箱", u"ふでばこ")
#    print_verbose(u"人人", u"ひとびと")
#    print_verbose(u"岸壁", u"がんぺき")
#    print_verbose(u"一つ", u"ひとつ")
#    print_verbose(u"別荘", u"べっそう")
#    print_verbose(u"出席", u"しゅっせき")
#    print_verbose(u"分別", u"ふんべつ")   
#    print_verbose(u"刈り入れ人", u"かりいれびと")
#    print_verbose(u"日帰り", u"ひがえり")        
#    print_verbose(u"アリドリ科", u"ありどりか")
#    print_verbose(u"赤鷽", u"アカウソ")
#    print_verbose(u"重立った", u"おもだった")
#    print_verbose(u"刈り手", u"かりて")
#    print_verbose(u"働き蟻", u"はたらきあり")
#    print_verbose(u"往き交い", u"いきかい")    
#    print_verbose(u"積み卸し", u"つみおろし")
#    print_verbose(u"包み紙", u"つつみがみ")
#    print_verbose(u"守り人", u"もりびと")
#    print_verbose(u"糶り", u"せり")       
#    print_verbose(u"バージョン", u"バージョン")
#    print_verbose(u"シリアルＡＴＡ", u"シリアルエーティーエー")
#    print_verbose(u"自動金銭出入機", u"じどうきんせんしゅつにゅうき")
#    print_verbose(u"全国津々浦々", u"ぜんこくつつうらうら")
#    print_verbose(u"作り茸", u"ツクリタケ")     
#    print_verbose(u"別荘", u"ベッソウ")
#    print_verbose(u"守り人", u"モリビト")
#    print_verbose(u"建て替える", u"タテカエル")
#    print_verbose(u"一つ", u"ヒトツ")
#    
#    print_verbose(u'先程',u'サキホド')
#    print_verbose(u'先程',u'さきほど')
#    
#    print_verbose(u'先週',u'センシュウ')
#    print_verbose(u'先週',u'せんしゅう')
#
#    print_verbose(u'姉さん',u'ネエサン')
#    print_verbose(u'姉さん',u'ねえさん')
#
#    print_verbose(u'近寄る',u'チカヨル')
#    print_verbose(u'近寄る',u'ちかよる')
#
#    print_verbose(u'弱気',u'ヨワキ')
#    print_verbose(u'弱気',u'よわき')
#
#    print_verbose(u'あの',u'アノ')
#    print_verbose(u'アノ',u'あの')
#    print_verbose(u'明かん',u'あかん')
#
#    print_verbose(u'人となり',u'ひととなり')
#    print_verbose(u'陰',u'かげ')
#
#    print_verbose(u'寛',u'ゆた')    
#    
#    print_verbose(u'高じる',u'こうじる')
#    print_verbose(u'コーヒーの木',u'コーヒーのき') 
#    print_verbose(u'突っ立てる',u'つったてる')
#    print_verbose(u'尽し', u'づくし')
#    print_verbose(u'引篭り', u'ひきこもり')
#    print_verbose(u'金詰り',u'かねづまり')
    

#    print_all_verbose(u"結婚", u"けっこん")
    print_all_verbose(u"黒っぽい", u"くろっぽい")
    print_all_verbose(u"切戸", u"きれっと")


#    print_all_verbose(u'駆け巡る',u'かけめぐる')
#    
#    print_all_verbose(u'真向法',u'まっこうほう')
#    print_all_verbose(u'突掛ける',u'つっかける')
#    
#
#    print_all_verbose(u'偽小切手',u'ぎこぎって')


#    print_verbose(u'プログラム制御式及びキーボード制御式のアドレス指定可能な記憶域をもつ計算器',
#                  u'プログラムせいぎょしきおよびキーボードせいぎょしきのアドレスしていかのうなきおくいきをもつけいさんき')
   
