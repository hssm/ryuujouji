# -*- coding: utf-8 -*-

#Hiragana range is U+3041 to U+309F
HIRAGANA_START = ord(unicode('ぁ'))
HIRAGANA_END = ord(unicode('ゟ'))    
HIRAGANA_RANGE = range(HIRAGANA_START, HIRAGANA_END+1)

#Katakana range is U+30A0 to U+30FF
KATAKANA_START = ord(unicode('゠'))
KATAKANA_END = ord(unicode('ヿ'))
KATAKANA_RANGE = range(KATAKANA_START, KATAKANA_END+1)

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
