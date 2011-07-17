# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt

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

    
if __name__ == '__main__':
    print kata_to_hira(u'あえいうおアエイウオ')
