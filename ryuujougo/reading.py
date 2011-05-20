# -*- coding: utf-8 -*-

import sys
import os
import re
import tools
import copy
import time
from sqlalchemy.sql import select, and_, or_
from sqlalchemy import create_engine, Table, Column, Unicode,\
                       String, Boolean, ForeignKey, MetaData
                       
READINGS_PATH = "../dbs/readings.sqlite"
JMDICT_PATH = "../dbs/jmdict.sqlite"
KANJIDIC_PATH = "../dbs/kanjidic.sqlite"

#Hiragana range is U+3041 to U+309F
HIRAGANA_START = ord(unicode('ぁ'))
HIRAGANA_END = ord(unicode('ゟ'))    
HIRAGANA_RANGE = range(HIRAGANA_START, HIRAGANA_END+1)

#Katakana range is U+30A0 to U+30FF
KATAKANA_START = ord(unicode('゠'))
KATAKANA_END = ord(unicode('ヿ'))
KATAKANA_RANGE = range(KATAKANA_START, KATAKANA_END+1)

r_meta = MetaData()
r_engine = None

reading_t = Table('reading', r_meta,
			Column('character', Unicode, primary_key=True),
			Column('reading', Unicode, primary_key=True),
			Column('type', String, primary_key=True),
			Column('affix', String, primary_key=True),
			Column('has_okurigana', Boolean, nullable=False))

def init():
	global r_engine
	global r_meta
	
	if not os.path.exists(READINGS_PATH):
		if not os.path.exists(KANJIDIC_PATH):
			print "No kanjidic database found at %s" % KANJIDIC_PATH
			print "Cannot continue without it."
			return
		r_engine = create_engine('sqlite:///'+READINGS_PATH)
		r_meta.create_all(r_engine)
		db_populate_readings()
	else:
		r_engine = create_engine('sqlite:///'+READINGS_PATH)
	
def db_populate_readings():
	kd_engine = create_engine('sqlite:///'+KANJIDIC_PATH)
	kd_meta = MetaData()
	kd_meta.bind = kd_engine
	kd_meta.reflect()

	kd_reading = kd_meta.tables['reading']
	kd_nanori = kd_meta.tables['nanori']
		
	reading_l = []
	n_to_save = 500
	n = 0
	start = time.time()

	s = select([kd_reading], or_(kd_reading.c['r_type'] == 'ja_on',
								 kd_reading.c['r_type'] == 'ja_kun'))
	readings = kd_engine.execute(s)
	for r in readings:
		affix = "none"
		reading = r.reading
		if r.reading[-1] == "-":
			affix = "prefix"
			reading = reading[:-1]
		elif r.reading[0] == "-":
			affix = "suffix"
			reading = reading[1:]
			
		has_oku = False
		if "." in r.reading:
			has_oku = True
			
		reading_l.append({'character':r.character_literal,
						  'reading':reading,
						  'type':r.r_type,
						  'affix':affix,
						  'has_okurigana':has_oku})
		
	s = select([kd_nanori])
	nanori = kd_engine.execute(s)
	
	for n in nanori:
		reading_l.append({'character':n.character_literal,
						  'reading':n.nanori,
			 			  'type':'nanori',
			 			  'affix':'none',
			 			  'has_okurigana':False})
		
	r_engine.execute(reading_t.insert(), reading_l)
	print 'Filling database with kanji/reading data took '\
	  	  '%s seconds' % (time.time() - start)


def get_words_with_reading(kanji, kd_reading, words):
	print "Kanji: %s  --  Reading: %s" % (kanji, kd_reading)
	for entry in words:
		(word, w_reading, usage, meaning) = entry	
		
		for char in word:
			if ord(char) in HIRAGANA_RANGE or ord(char) in KATAKANA_RANGE:
				pass
			else:
				try:
					readings = get_individual_readings(str(char))
				except:
					print "DIED ON %s" % char
					#readings = get_individual_readings(str(char))
				
		#if reading in w_reading:
			#print word, w_reading, usage, meaning




def get_individual_readings(word, reading, segments=[], found="", solutions=[]):
	if len(word) == 0:
		print "Nothing left to solve. Appending this one as a solution." 
		solutions.append(segments)
	else:
		print "Solving: %s  =  %s \t\t <--> Current attempt = %s"  % (word, reading, found)
		
	#for char in word:
	if len(word) > 0:
		char = word[0]
		if ord(char) in HIRAGANA_RANGE or ord(char) in KATAKANA_RANGE:
			#if ord(char) in KATAKANA_RANGE:
			#	char = tools.kata_to_hira(char)
			if len(reading) == 0:
				print "No readings left to match. Part of word left: ", word
			else:
				if char == reading[0]:
					print "--> Removed:  " + char
					tmp_found = found+char
					tmp_word = word[1:]
					tmp_reading = reading[1:]
					tmp_segments = copy.copy(segments)
					tmp_segments.append([char, char])
					get_individual_readings(tmp_word, tmp_reading, tmp_segments, tmp_found, solutions)
				else:
					print "%s is definitely not %s. Abort attempt." % (char, reading[0])
		else:

			s = select([reading_t], reading_t.c['character'] == char)
			char_readings = r_engine.execute(s).fetchall()
			
			print "Character found: = " + char
			
			if char_readings == None:	#TODO: Handle non-kanji and non-kana characters
				print "Need to abort gracefully!"
				return None
			for r in char_readings:
				print "\t " + r.reading +  "\t " + r.affix + "\t" + str(r.has_okurigana)
				
			for cr in char_readings:
				#print "\t " + r.reading + "\t" + r.affix + "\t" + str(r.has_okurigana)
						
				if cr.has_okurigana == True:
					(r, s, o) = cr.reading.partition(".") #reading, separator, okurigana
					

					rl = len(r)
					ol = len(o)
					ot = word[1:ol+1] #the portion we want to test as okurigana
					
					if r == reading[:rl] and ot == o:
						print "Match found for reading %s with okurigana %s" % (r, o)
						tmp_found = found + r + o
						tmp_word = word[ol+1:]
						tmp_reading = reading[ol+rl:]
						tmp_segments = copy.copy(segments)
						tmp_segments.append([char, r])
						tmp_segments.append([o, o])
						get_individual_readings(tmp_word, tmp_reading, tmp_segments, tmp_found, solutions)				
				else:
					r = cr.reading
					rl = len(r)
					#we deal with readings in hiragana, so convert from katakana if it exists
					if ord(r[0]) in KATAKANA_RANGE:
						r = tools.kata_to_hira(r)
												
					if reading.startswith(r):
						print "Match found for reading %s: starting with %s" % (reading, r)
						tmp_found = found + r
						tmp_word = word[1:]
						tmp_reading = reading[rl:]
						tmp_segments = copy.copy(segments)
						tmp_segments.append([char, r])
						get_individual_readings(tmp_word, tmp_reading, tmp_segments, tmp_found, solutions)
			print "No further parsing possible for reading starting with %s and ending with %s.\n\t Up one level." % (found, word)
	return solutions
	
		
if __name__ == "__main__":
	if False:		
		try:
			os.remove(READINGS_PATH)
		except:
			pass
	init()
	#db_populate_words_by_reading()

#	soltions = get_individual_readings(u"小牛", u"こうし")
#	soltions = get_individual_readings(u"お腹", u"おなか")
#	soltions = get_individual_readings(u"バス停", u"バスてい")
#	soltions = get_individual_readings(u"一つ", u"ひとつ")
#	soltions = get_individual_readings(u"非常事態", u"ひじょうじたい")
	soltions = get_individual_readings(u"建て替える", u"たてかえる")
#	soltions = get_individual_readings(u"今日", u"きょう")
#	soltions = get_individual_readings(u"小さい", u"ちいさい")
#	soltions = get_individual_readings(u"鉄道公安官", u"てつどうこうあんかん")
#	soltions = get_individual_readings(u"日帰り", u"ひがえり")
	print "\n\n"
	for i,sol in enumerate(soltions):
		print "Solution #", i
		for s in sol:
			print s[0] + " -- " + s[1]
#	db_populate_words_by_reading()