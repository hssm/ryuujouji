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
last_char = {}

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

def get_variants(reading):
    variant_list = []
    
    first = reading[0]
    last = reading[-1]

    #The original reading
    variant_list.append((reading, SegmentTag.Regular))
    
    first_list = []

    if first in first_char:
        for (kana, tag) in first_char[first]:
            v = (kana+reading[1:], tag)
            variant_list.append(v)
            first_list.append(v)
    if last in last_char:
        for (kana, tag) in last_char[last]:
            v = (reading[:-1]+kana, tag)
            variant_list.append(v)
            
            #also add variants with both first and last character modified
            for var in first_list:
                v = (var[0][:-1]+kana, tag)
                variant_list.append(v)
        
    #manual addition of sokuon at the end
    if is_hira(reading[0]):
        soku = u'っ'
    else:
        soku = u'ッ'
        
    v = (reading[:-1]+soku, SegmentTag.Sokuon)
    variant_list.append(v)
    for var in first_list:
        v = (var[0][:-1]+soku, tag)
        variant_list.append(v)
            
    return variant_list

def get_oku_variants(okurigana):
    oku_variant_list = []
    
    #Figure out all okurigana variations so we can attach them to each reading
    if len(okurigana) > 0:
        #Add the original one
        oku_variant_list.append((okurigana, SegmentTag.OkuRegular,
                                           len(okurigana)))
        
        oku_last_k = okurigana[-1]
        if oku_last_k in oku_last_char:
            for (oku, tag) in oku_last_char[oku_last_k]:
                oku_variant_list.append((okurigana[:-1]+oku, tag, len(oku)))

    return oku_variant_list
                        