#!/usr/bin/env python

import tweepy
from tweepy.streaming import Stream, StreamListener
import json
import ConfigParser
import re
import sys
import time
from unicodedata import normalize
from HTMLParser import HTMLParser

# used for timestamped logs
starttime = time.strftime('%Y%m%d-%H%M%S')

def tweettime2unix(x):
	'''convert twitter's wacky timestamp into unix time'''
	return time.mktime( time_parser(x).timetuple() )

def tweet_time(tweet):
	'''extract time from tweet'''
	t_time = 0
	if 'timestamp_ms' in tweet:
		t_time = int(tweet['timestamp_ms']) / 1000.0
	else:
		t_time = tweettime2unix(tweet['created_at'])
	return time.strftime("%Y%m%d.%H%M%S", time.localtime(t_time))

hp = HTMLParser()
def sanitize(x):
	'''convert fancy unicode to ascii'''
	return hp.unescape( normalize('NFKD', u'%s' % x ).encode('ascii','ignore') )

def urlfix(body, tweet):
	'''un-shorten stupid t.co links'''
	for X in tweet[u'entities'][u'urls']:
		old = X[u'url']
		new = X[u'expanded_url']
		body = body.replace(old, new)

	if 'extended_entities' in tweet:
		for X in tweet[u'extended_entities'][u'media']:
			old = X[u'url']
			new = X[u'media_url']
			body = body.replace(old, new)

	return body


def tweetparse(tweet, src_account='.', db=None):
	if 'retweeted_status' in tweet:
		try:
			tweetparse(tweet[u'retweeted_status'])
		except:
			pass

	if 'text' not in tweet:
		return

	t_time = tweet_time(tweet)
	t_id = tweet['id']
	t_lang = tweet['lang']
	t_txt = sanitize(tweet['text'] )

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
	'''
	db.execute('INSERT OR REPLACE into users (id, screen_name, name, descr, lang, time_zone, utc_offset, location) VALUES (?,?,?,?,?,?,?,?)', (u_id, u_handle, u_name, u_descr, u_lang, u_tz, u_utcoff, u_location))
	db.execute('INSERT OR REPLACE into tweets (id, timestamp, user_id, lang, src_account, text) VALUES (?,?,?,?,?,?)', (t_id, t_time, u_id, t_lang, src_account, t_txt))
	db.commit()
	'''
	print "[%s] %s <%s> %s" % ( t_time, src_account, u_handle, t_txt)

class StreamPrinter(StreamListener):
	def __init__(self):
		self.data_fd = open('firehose_log.%s.json' % starttime, 'a')
		self.db = None
		
	def on_data(self, data):
		try:
			tweet = json.loads(data)
		except:
			return # invalid json

		self.data_fd.write(data) # valid json, log it.

		if tweet.keys() == [u'friends']:
			return # not interested in "friends" packet

		if u'text' not in tweet:
			return # not a tweet we can handle

		try:
			tweetparse(tweet)
		except:
			pass

		return True
# End of "class StreamPrinter"

def twitter_auth(user, config):
	auth = tweepy.OAuthHandler( config.get('firehose', 'consumer_key'), config.get('firehose', 'consumer_secret'))
	auth.set_access_token( config.get(user, 'key'), config.get(user, 'secret') )
	return auth

def check_login(user, auth):
	api = tweepy.API(auth)
	if (api.me().screen_name.lower() == user.lower()):
		return True
	else:
		return False

def main():
	config = ConfigParser.ConfigParser()
	if len(sys.argv) > 2:
		conf = sys.argv[1]
	else :
		conf = 'firehose.ini'
	config.read(conf)

	user = config.get('firehose', 'user')
	keywords = config.get('firehose', 'keywords')
	auth = twitter_auth(user, config)
	if check_login(user, auth) == False:
		sys.exit(0)

	try:
		twitterStream = Stream(auth, StreamPrinter())
		twitterStream.filter(track = keywords)
	except:
		twitterStream.disconnect()

if __name__ == '__main__':
	main()
