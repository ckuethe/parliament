#!/usr/bin/env python

import tweepy
from tweepy.streaming import Stream, StreamListener
#from pysqlite2 import dbapi2 as sqlite
import anyjson
from HTMLParser import HTMLParser
import ConfigParser
import re
import os
import sys
import time

class StreamPrinter(StreamListener):
	def __init__(self):
		self.outfd = open('parliament_log.' + time.strftime('%Y%m%d-%H%M%S') + '.json', 'a')
		self.hp = HTMLParser()

	def on_data(self, data):
		self.outfd.write(data)
		try:
			t = anyjson.deserialize(data)
			txt = re.sub(r'[^\x00-\x7f]',r'_', self.hp.unescape(t['text'].encode('ascii')))
			print "[%s] %s >> %s" % ( t['created_at'], t['user']['screen_name'], txt )
		except ValueError:
			pass
		return True

	def on_error(self, status):
		print status

if __name__ == '__main__':
	config = ConfigParser.ConfigParser()
	config.readfp(open('parliament.ini'))

	s = config.sections()
	if 'General' not in s:
		print 'Config file must contain [General] section'
		sys.exit(1)

	users = config.get('General', 'users').replace(",", " ").split()
	if len(users) is 0:
		print 'no accounts configured'
		sys.exit(1)
	else:
		user = users[0]

	consumer_key = config.get('General', 'consumer_key')
	consumer_secret = config.get('General', 'consumer_secret')
	keywords = config.get('General', 'keywords')
	if keywords is not None and len(keywords):
		keywords = keywords.replace(",", " ").split()
	else:
		keywords = []
	print keywords

	auth = tweepy.OAuthHandler(consumer_key, consumer_secret, secure=True)
	auth.set_access_token(config.get(user, 'key'), config.get(user, 'secret') )

	api = tweepy.API(auth)
	print "I am " + api.me().screen_name
	try:
		twitterStream = Stream(auth, StreamPrinter())
		twitterStream.filter(track = keywords)
		#tweepy.debug(True, 4)
		#twitterStream.userstream(_with='user')
	except KeyboardInterrupt:
		twitterStream.disconnect()
