# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import copy
from segments import SegmentTag 
from tools import is_hira

HAS_DAKUTEN_LIST = list(u'かきくけこたちつてとさしすせそはひふへほ'
                        u'カキクケコタチツテトサシスセソハヒフヘホ')

HAS_HANDAKUTEN_LIST = list(u'はひふへほハヒフヘホ') 


class Variant:
    
    def __init__(self, reading, taglist):
        self.reading = reading      
        self.length = len(reading)
        self.tags = taglist
        
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
oku_last_char[u'る'].append((u'', SegmentTag.OkuRegular)) 

def get_variants(dic_reading):
    #Variants we are still building (or building from)
    base_list = []
    
    #The final vairant list
    variant_list = []
    
    (reading, sep, okurigana) = dic_reading.partition('.')
    first = reading[0]
    o_variants = get_oku_variants(okurigana)
    
    #The original reading
    v = Variant(reading, [SegmentTag.Regular])
    base_list.append(v)
   
    #Add all base variants with a change in the first character 
    if first in first_char:
        for (kana, tag) in first_char[first]:
            new_r = kana+reading[1:]
            v = Variant(new_r, [tag])
            base_list.append(v)


    if is_hira(first):
        soku = u'っ'
    else:
        soku = u'ッ'
    
    tmp_list = []
    
    #Create more base variants by replacing the last character of the ones
    #we have so far with a sokuon
    for var in base_list:
        if len(var.reading) > 1: 
            new_r = var.reading[:-1]+soku
            
            #existing tags of this base variant + the new one
            tags = copy.copy(var.tags)
            tags.append(SegmentTag.Sokuon)
            v = Variant(new_r, tags)
            tmp_list.append(v)
    
    base_list.extend(tmp_list)

    if len(okurigana) > 0:
        
        #add every oku variant to every variant from above
        for var in base_list:
            for ovar in o_variants:
                tags =  copy.copy(var.tags)
                tags.extend(ovar.tags)
                v = Variant(var.reading+ovar.reading, tags)
                variant_list.append(v)

    else:
        variant_list = base_list
    
    return variant_list

def get_oku_variants(okurigana):
    oku_vars = []
    
    if len(okurigana) > 0:
        #Add the original one
        v = Variant(okurigana, [SegmentTag.OkuRegular])
        oku_vars.append(v)

        #also add variant with っ instead of last char
        new_oku = okurigana[:-1]+u'っ'
        v = Variant(new_oku, [SegmentTag.OkuSokuon])
        oku_vars.append(v)
        
        oku_last_k = okurigana[-1]
        if oku_last_k in oku_last_char:
            for (oku, tag) in oku_last_char[oku_last_k]:
                new_oku = okurigana[:-1]+oku
                v = Variant(new_oku, [tag])
                oku_vars.append(v)
        
    return oku_vars
                        