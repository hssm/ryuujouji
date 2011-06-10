# -*- coding: utf-8 -*-
#Copyright (C) 2011 Houssam Salem <ntsp.gm@gmail.com>
#License: GPLv3; http://www.gnu.org/licenses/gpl.txt
import time
from sqlalchemy import MetaData
from sqlalchemy.sql import select, bindparam
from reading import get_readings
import db

conn = db.get_connection()
meta = MetaData()
meta.bind = conn.engine
meta.reflect()
word_t = meta.tables['word']
segment_t = meta.tables['segment']
tag_t = meta.tables['tag']

found_l = []
segment_l = []
tag_l = []

def save_found():
    global found_l
    global segment_l
    global tag_l
    
    u = word_t.update().where(word_t.c['id']==
                              bindparam('word_id')).\
                              values(found=bindparam('found'))
    conn.execute(u, found_l)
    conn.execute(segment_t.insert(), segment_l)
    conn.execute(tag_t.insert(), tag_l)
    found_l = []    
    segment_l = []
    tag_l = []


def fill_solutions():
    start = time.time()
    conn.execute(segment_t.delete())
    s = select([word_t])
    words = conn.execute(s).fetchall()
    goal = len(words)
    save_now = 0
    total = 0

    seg_id = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        for seg in segments:
            seg_id += 1
            #print 'seg == ' , seg.unit
            found_l.append({'word_id':word.id, 'found':True})
            segment_l.append({'id':seg_id,
                              'word_id':word.id,
                              'reading_id':seg.reading_id,
                              'nth_kanji':seg.nth_kanji,
                              'nth_kanjir':seg.nth_kanjir})
            for tag in seg.tags:
                tag_l.append({'segment_id':seg_id,
                              'tag':tag})

        save_now += 1
        if save_now > 20000:
            save_now = 0
            save_found()
            total += 20000
            print "Progress %s %% in %s seconds" % ((float(total) / goal)*100,
                                                    (time.time() - start))
    save_found()
    print 'took %s seconds' % (time.time() - start)

def dry_run():
    """Don't save any changes to the database, but check if the present
     parsing behaviour breaks the solving of an already-solved entry.
     """
     
    start = time.time()
    s = select([word_t])
    words = conn.execute(s)
    newly_solved = 0
    for word in words:
        segments = get_readings(word.keb, word.reb)
        if word.found == True:
            if len(segments) == 0:
                print "Regression for word %s == %s" %(word.keb, word.reb)
        else:
            if len(segments) > 0:
                newly_solved += 1
                print "New found word %s" % word.keb, word.reb
    print "The changes will solve another %s entries. " % newly_solved


def print_stats():
    s = select([word_t])
    words = conn.execute(s).fetchall()
    n = len(words)
    
    s = select([word_t], word_t.c['found'] == True)
    found = conn.execute(s).fetchall()
    nf = len(found)
    
    percent = float(nf) / float(n) * 100
    print "There are %s entries in JMdict. A solution has been found for %s"\
          " of them. (%d%%)" % (n, nf, percent)

def testme(k, r):
    print
    print "Solving: %s == %s" % (k, r)
    segments = get_readings(k, r)

    for s in segments:
        print 'character[%s]' % s.character,
        print 'reading[%s]' % s.reading,
        print 'nth_kanji[%s]' % s.nth_kanji,
        print 'nth_kanjir[%s]' % s.nth_kanjir,
        print 'tags%s' % s.tags,
        print 'dic_reading[%s]' % s.dic_reading,
        print 'reading_id[%s]' % s.reading_id,
        print


if __name__ == "__main__":
    testme(u'漢字', u'かんじ')
    testme(u"小牛", u"こうし")
    testme(u"バス停", u"バスてい")
    testme(u"非常事態", u"ひじょうじたい")
    testme(u"建て替える", u"たてかえる")
    testme(u"小さい", u"ちいさい")
    testme(u"鉄道公安官", u"てつどうこうあんかん")
    testme(u"手紙", u"てがみ")
    testme(u"筆箱", u"ふでばこ")
    testme(u"人人", u"ひとびと")
    testme(u"岸壁", u"がんぺき")
    testme(u"一つ", u"ひとつ")
    testme(u"別荘", u"べっそう")
    testme(u"出席", u"しゅっせき")
    testme(u"結婚", u"けっこん")
    testme(u"分別", u"ふんべつ")   
    testme(u"刈り入れ人", u"かりいれびと")
    testme(u"日帰り", u"ひがえり")        
    testme(u"アリドリ科", u"ありどりか")
    testme(u"赤鷽", u"アカウソ")
    testme(u"重立った", u"おもだった")
    testme(u"刈り手", u"かりて")
    testme(u"働き蟻", u"はたらきあり")
    testme(u"往き交い", u"いきかい")    
    testme(u"積み卸し", u"つみおろし")
    testme(u"包み紙", u"つつみがみ")
    testme(u"守り人", u"もりびと")
    testme(u"糶り", u"せり")       
    testme(u"バージョン", u"バージョン")
    testme(u"シリアルＡＴＡ", u"シリアルエーティーエー")
    testme(u"自動金銭出入機", u"じどうきんせんしゅつにゅうき")
    testme(u"作り茸", u"ツクリタケ")    
    testme(u"全国津々浦々", u"ぜんこくつつうらうら")     
    testme(u"別荘", u"ベッソウ")
    testme(u"守り人", u"モリビト")
    testme(u"建て替える", u"タテカエル")
    testme(u"一つ", u"ヒトツ")
#    fill_solutions() 
#    print_stats()     
#    dry_run()

#    testme(u"燃やす", u"もす")
#    testme(u"酒機嫌", u"ささきげん")
#    testme(u"四日市ぜんそく", u"よっかいちぜんそく")
#    testme(u"お腹", u"おなか")
#    testme(u"今日", u"きょう")
#    testme(u"当り", u"あたり")


#^Updated JMdict
#There are 159247 entries in JMdict. A solution has been found for 131473 of them. (82%)
#There are 159203 entries in JMdict. A solution has been found for 131416 of them. (82%)
