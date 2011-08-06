# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

from segments import SegmentTag 
from tools import is_hira

HAS_DAKUTEN_LIST = list(u'かきくけこたちつてとさしすせそはひふへほ'
                        u'カキクケコタチツテトサシスセソハヒフヘホ')

HAS_HANDAKUTEN_LIST = list(u'はひふへほハヒフヘホ') 

first_char = {}
oku_last_char = {}


#We know the order we are inserting the dictionary keys, so there is no need
#to check their existence first.

for kana in HAS_DAKUTEN_LIST:
    kana_daku = unichr(ord(kana)+1)
    first_char[kana] = [(kana_daku, SegmentTag.Dakuten)]

#special cases 
tag = SegmentTag.Dakuten
first_char[u'ち'].append((u'じ', tag))
first_char[u'つ'].append((u'ず', tag))
first_char[u'チ'].append((u'ジ', tag))
first_char[u'ツ'].append((u'ズ', tag))

for kana in HAS_HANDAKUTEN_LIST:
    kana_handaku = unichr(ord(kana)+2)
    first_char[kana].append((kana_handaku, SegmentTag.Handakuten))


#Note: there are no katakana okurigana (in kanjidic) 
tag = SegmentTag.OkuInflected
oku_last_char[u'む'] = [(u'み', tag)]
oku_last_char[u'ぬ'] = [(u'に', tag)]
oku_last_char[u'る'] = [(u'り', tag)]
oku_last_char[u'う'] = [(u'い', tag)]
oku_last_char[u'ぐ'] = [(u'ぎ', tag)]
oku_last_char[u'ぶ'] = [(u'び', tag)]
oku_last_char[u'く'] = [(u'き', tag)]
oku_last_char[u'す'] = [(u'し', tag)]
oku_last_char[u'つ'] = [(u'ち', tag)]


oku_last_char[u'つ'].append((u'っ', SegmentTag.OkuSokuon))
oku_last_char[u'る'].append((u'', 'RuTrim')) 

def get_variants(dic_reading):
    variant_list = []
    (reading, sep, okurigana) = dic_reading.partition('.')
    
    first = reading[0]
    oku_var_list = get_oku_variants(okurigana)
    
    #The original reading
    variant_list.append((reading, SegmentTag.Regular, len(reading)))
  
    rl = len(reading)
  
    if first in first_char:
        for (kana, tag) in first_char[first]:
            new_r = kana+reading[1:] 
            v = (new_r, tag, rl)
            variant_list.append(v)
               
    if is_hira(first):
        soku = u'っ'
    else:
        soku = u'ッ'
    
    tmp_list = []
    
    #add end sokuon to each variant (non-oku so far)
    for var in variant_list:
        if len(var[0]) > 1: 
            new_r = var[0][:-1]+soku 
            v = (new_r, 'read_end_sok', rl)
            tmp_list.append(v)
    
    variant_list.extend(tmp_list)
    
    tmp_list = []
    
    #add every oku variant to every variant from above
    for (var, tag, rl) in variant_list:
        for (ovar, otag, ovl) in oku_var_list:
            v = (var+ovar, 'zzz', len(var+ovar))
            tmp_list.append(v)
    variant_list.extend(tmp_list)
    
    return variant_list

def get_oku_variants(okurigana):
    oku_vars = []
    
    if len(okurigana) > 0:
        #Add the original one
        oku_vars.append((okurigana, SegmentTag.OkuRegular, len(okurigana)))

        #also add variant with っ instead of last char
        new_oku = okurigana[0][:-1]+u'っ'
        oku_vars.append((new_oku, 'test', len(new_oku)))
        
        oku_last_k = okurigana[-1]
        if oku_last_k in oku_last_char:
            for (oku, tag) in oku_last_char[oku_last_k]:
                new_oku = okurigana[:-1]+oku
                oku_vars.append((new_oku, tag, len(new_oku)))
        



    return oku_vars
                        