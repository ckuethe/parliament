#!/usr/bin/env python

import sys
import pprint
import re
from dateutil.parser import parse as time_parser
from HTMLParser import HTMLParser
from unicodedata import normalize
import ConfigParser
import sqlite3

hp = HTMLParser()
pp = pprint.PrettyPrinter()

config = ConfigParser.ConfigParser()
config.read('parliament.ini')
db = sqlite3.connect(config.get('General', 'database'))

def raw_dot():
	sys.stdout.write('.')
	sys.stdout.flush()

def tweettime2unix(x):
	'''convert twitter's wacky timestamp into unix time'''
	return time.mktime( time_parser(x).timetuple() )

def sanitize(x):
	return hp.unescape( normalize('NFKD', u'%s' % x ).encode('ascii','ignore') )

def tweetparse(tweet):
	if 'retweeted_status' in tweet:
		try:
			tweetparse(tweet['retweeted_status'])
		except:
			pass

	if 'created_at' not in tweet:
		return

	t_time = 0
	if 'timestamp_ms' in tweet:
		t_time = int(tweet['timestamp_ms']) / 1000.0
	else:
		t_time = tweettime2unix(tweet['created_at'])
	t_id = tweet['id']
	t_lang = tweet['lang']
	t_txt = hp.unescape( normalize('NFKD', u'%s' % tweet['text'] ).encode('ascii','ignore') )
	# coordinates, geo, place

	u_id = tweet['user']['id']
	u_lang = tweet['user']['lang']
	u_tz = tweet['user']['time_zone']
	u_utcoff = (tweet['user']['utc_offset'] or 0) / 3600
	u_location = sanitize(tweet['user']['location'])
	u_handle = tweet['user']['screen_name']
	u_name = sanitize(tweet['user']['name'])
	u_descr = sanitize(tweet['user']['description'])
	
	# http://paulgatterdam.com/blog/?p=121
	db.execute('INSERT OR REPLACE into users (id, screen_name, name, descr, lang, time_zone, utc_offset, location) VALUES (?,?,?,?,?,?,?,?)', (u_id, u_handle, u_name, u_descr, u_lang, u_tz, u_utcoff, u_location))
	db.execute('INSERT OR REPLACE into tweets (id, timestamp, user_id, lang, text) VALUES (?,?,?,?,?)', (t_id, t_time, u_id, t_lang, t_txt))
	#print "[%d] %s >> %s" % ( t_time, u_handle, t_txt )

def main():
	linecounter = 0
	for f in sys.argv[1:] :
		print "open(%s)" % f
		fd = open(f, 'r')
		for js in fd.readlines() :
			try:
				tweet = json.loads(js)
				tweetparse(tweet)
			except ValueError, KeyError:
				pass
			linecounter += 1
			if linecounter > 250:
				linecounter = 0
				raw_dot()
				db.commit()
		fd.close()
		print ""
		db.commit()

if __name__ == '__main__':
	main()
