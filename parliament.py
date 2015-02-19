#!/usr/bin/env python

import threading
import sqlite3
import tweepy
from tweepy.streaming import Stream, StreamListener
import json
import ConfigParser
import re
import sys
import time
from dateutil.parser import parse as time_parser
from unicodedata import normalize
from HTMLParser import HTMLParser

# used for timestamped logs
starttime = time.strftime('%Y%m%d-%H%M%S')

def sanitize(x):
	'''convert fancy unicode to ascii'''
	hp = HTMLParser()
	return hp.unescape( normalize('NFKD', u'%s' % x ).encode('ascii','ignore') )

def urlfix(body, tweet):
	'''un-shorten stupid t.co links'''
	for X in tweet[u'entities'][u'urls']:
		old = X[u'url']
		new = X[u'expanded_url']
		body = body.replace(old, new)

	return body

def tweetparse(user, db, tweet):
	if 'retweeted_status' in tweet:
		try:
			tweetparse(user, db, tweet[u'retweeted_status'])
		except:
			pass

	if 'text' not in tweet:
		return

	t_time = 0
	if 'timestamp_ms' in tweet:
		t_time = int(tweet['timestamp_ms']) / 1000.0
	else:
		t_time = time.mktime(time_parser(tweet['created_at']).timetuple())
	t_id = tweet['id']
	t_lang = tweet['lang']
	t_txt = hp.unescape( normalize('NFKD', u'%s' % tweet['text'] ).encode('ascii','ignore') )

	if len(tweet[u'entities'][u'urls']):
		t_txt = urlfix(t_txt, tweet)
	# XXX figure out what to do about geotags: coordinates, geo, place

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
	db.execute('INSERT OR REPLACE into tweets (id, timestamp, user_id, lang, src_account, text) VALUES (?,?,?,?,?,?)', (t_id, t_time, u_id, t_lang, user, t_txt))
	db.commit()
	print "[%s] %s <%s> %s" % ( tweet['created_at'], user, u_handle, t_txt)


class myStreamListener(StreamListener):
	def __init__(self):
		self.data_fd = None
		self.db = None
		self.user = None

	def on_connect(self):
		self.data_fd = open('streamthread_log.%s.%s.json' % (starttime, self.user), 'a')

	def on_data(self, data):
		try:
			tweet = json.loads(data)
		except:
			return

		if tweet.keys() == [u'friends']: # not interested
			return

		self.data_fd.write(data) # valid useful json, log it.
		self.data_fd.flush()

		if 'text' not in tweet:
			return # not a tweet worth decoding

		try:
			tweetparse(self.user, self.db, tweet)
		except:
			pass

def twitter_auth(user, config):
	auth = tweepy.OAuthHandler( config.get('General', 'consumer_key'), config.get('General', 'consumer_secret'))
	auth.set_access_token( config.get(user, 'key'), config.get(user, 'secret') )
	return auth

def check_login(user, auth):
	api = tweepy.API(auth)
	if (api.me().screen_name.lower() == user.lower()):
		return True
	else:
		return False

def stream_thread(user, config):
	auth = twitter_auth(user, config)
	if check_login(user, auth) == False:
		sys.exit(0)

	twitterStream = Stream(auth, myStreamListener())
	twitterStream.listener.db = sqlite3.connect(config.get('General', 'database'))
	twitterStream.listener.user = user

	try:
		twitterStream.userstream()
	except:
		twitterStream.listener.db.disconnect()
		twitterStream.disconnect()
		sys.exit(0)

def main():
	config = ConfigParser.ConfigParser()
	config.read('parliament.ini')

	threads = []
	for user in config.get('General', 'users').replace(",", " ").split():
		t = threading.Thread(name=user, target=stream_thread, args=(user,config,))
		threads.append(t)
		t.start()

	while 1:
		time.sleep(0.2)

if __name__ == '__main__':
	main()
