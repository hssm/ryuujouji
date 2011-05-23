# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

#Hiragana range is U+3041 to U+309F
HIRAGANA_START = ord(unicode('ぁ'))
HIRAGANA_END = ord(unicode('ゟ'))    
HIRAGANA_RANGE = range(HIRAGANA_START, HIRAGANA_END+1)

#Katakana range is U+30A0 to U+30FF
KATAKANA_START = ord(unicode('゠'))
KATAKANA_END = ord(unicode('ヿ'))
KATAKANA_RANGE = range(KATAKANA_START, KATAKANA_END+1)

KANA_RANGE = range(HIRAGANA_START, KATAKANA_END+1)

def is_kata(s):
    if len(s) > 0:
        for char in s:
            if ord(char) not in KATAKANA_RANGE:
                return False
        return True
    else:
        return False

def is_hira(s):
    if len(s) > 0:
        for char in s:
            if ord(char) not in HIRAGANA_RANGE:
                return False
        return True
    else:
        return False

def is_kana(s):
    if len(s) > 0:
        for char in s:
            if ord(char) not in KANA_RANGE:
                return False
        return True
    else:
        return False

def kata_to_hira(kata): 
    hira = ""
    for char in unicode(kata):
        hira += unichr(ord(char)-96)
    return hira

def hira_to_kata(hira): 
    kata = ""
    for char in unicode(hira):
        kata += unichr(ord(char)+96)
    return kata

def print_hira_kata():   
    for n in HIRAGANA_RANGE:
        sys.stdout.write(unichr(n))
    print ""
    for n in KATAKANA_RANGE:
        sys.stdout.write(unichr(n))

if __name__ == '__main__':
    #True
    print is_kana(u'バスてい')
    print is_hira(u'こんにちは')
    print is_kata(u'コンピューター')
    
    #False
    print is_kana(u'abc')
    print is_kana(u'新しい')    
    print is_hira(u'バスてい')
    print is_kata(u'きょう')
    print is_kata(u'きょうはスゴイ')
    