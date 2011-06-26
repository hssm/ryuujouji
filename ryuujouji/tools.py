# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

#Hiragana range is U+3041 to U+309F
#Katakana range is U+30A0 to U+30FF

HAS_DAKUTEN_LIST = list(u'かきくけこたちつてとさしすせそはひふへほカキクケコタチツテトサシスセソハヒフヘホ')
HAS_HANDAKUTEN_LIST = list(u'はひふへほハヒフヘホ') 


def is_kata(s):
    if s < u'\u30A0' or s > u'\u30FF':
        return False
    return True

def is_hira(s):
    if s < u'\u3041' or s > u'\u309F':
        return False
    return True

def is_kana(s):
    if s < u'\u3041' or s > u'\u30FF':
        return False
    return True

def hira_from_kata(char):
    if is_kata(char):
        return unichr(ord(char)-96)
    else:
        return char

def kata_from_hira(char):
    if is_hira(char):
        return unichr(ord(char)+96)
    else:
        return char

def kata_to_hira(s): 
    slist = [hira_from_kata(char) for char in s]
    s = "".join(slist)
    return s

def hira_to_kata(s):
    slist = [kata_from_hira(char) for char in s]
    s = "".join(slist)
    return s

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

def is_u(char):
    if char in [u'す',u'く', u'ぐ', u'む', u'ぶ', u'ぬ', u'る', u'う', u'つ']:
        return True
    
def u_to_i(char):
    if char == u'す':
        return u'し'
    elif char == u'く':
        return u'き'
    elif char == u'ぐ':
        return u'ぎ'
    elif char == u'む':
        return u'み'
    elif char == u'ぶ':
        return u'び'
    elif char == u'ぬ':
        return u'に'
    elif char == u'る':
        return u'り'
    elif char == u'う':
        return u'い'
    elif char == u'つ':
        return u'ち'
    
if __name__ == '__main__':

    print kata_to_hira(u'あえいうおアエイウオ')

    
    print get_dakuten(u'か')
    print get_dakuten(u'ほ')
    print get_dakuten(u'つ')
    
    print has_handakuten(u'ふ')
    print has_handakuten(u'へ')
    print get_handakuten(u'は')
    print get_handakuten(u'ひ')
    print get_handakuten(u'ほ')
