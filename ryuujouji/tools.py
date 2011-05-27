# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

import sys

#Hiragana range is U+3041 to U+309F
#Katakana range is U+30A0 to U+30FF

HAS_DAKUTEN_LIST = list(u'かきくけこたちつてとさしすせそはひふへほカキクケコタチツテトサシスセソハヒフヘホ')
HAS_HANDAKUTEN_LIST = list(u'はひふへほハヒフヘホ') 


def is_kata(kata):
    for s in kata:
        if s < u'\u30A0' or s > u'\u30FF':
            return False
    return True

def is_hira(hira):
    for s in hira:
        if s < u'\u3041' or s > u'\u309F':
            return False
    return True

def is_kana(kana):
    for s in kana:
        if s < u'\u3041' or s > u'\u30FF':
            return False
    return True

def kata_to_hira(s): 
    hira = ""
    for char in unicode(s):
        if is_kata(char):
            hira += unichr(ord(char)-96)
        else:
            hira += char
    return hira

def hira_to_kata(s):
    kata = ""
    for char in unicode(s):
        if is_hira(char):
            kata += unichr(ord(char)+96)
        else:
            kata += char
    return kata

def has_dakuten(kana):
    if kana in HAS_DAKUTEN_LIST:
        return True
    return False

def get_dakuten(kana):
    return unichr(ord(kana)+1)

def has_handakuten(kana):
    if kana in HAS_HANDAKUTEN_LIST:
        return True
    return False

def get_handakuten(kana):
    return unichr(ord(kana)+2)
    
def get_sokuon(kana):
    return unichr(ord(kana)-1)

if __name__ == '__main__':
    #True
    print is_kana(u'バスてい')
    print is_hira(u'こんにちは')
    print is_kata(u'コンピューター')
    print is_hira(kata_to_hira(u'あえいうおアエイウオ'))

    #False
    print is_kana(u'abc')
    print is_kana(u'新しい')    
    print is_hira(u'バスてい')
    print is_kata(u'きょう')
    print is_kata(u'きょうはスゴイ')
    
    print get_dakuten(u'か')
    print get_dakuten(u'ほ')
    print get_dakuten(u'つ')
    
    print has_handakuten(u'ふ')
    print has_handakuten(u'へ')
    print get_handakuten(u'は')
    print get_handakuten(u'ひ')
    print get_handakuten(u'ほ')
