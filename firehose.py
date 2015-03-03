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
from parliament_utils import *
import reverend.thomas

class StreamPrinter(StreamListener):
	def __init__(self):
		self.data_fd = None
		self.src_account = None
		self.classifier = None
		self.db = None
		
	def on_data(self, data):
		try:
			tweet = json.loads(data)
		except:
			return # invalid json

		if self.data_fd is not None:
			self.data_fd.write(data) # valid json, log it.

		if tweet.keys() == [u'friends']:
			return # not interested in "friends" packet

		if u'text' not in tweet:
			return # not a tweet we can handle

		try:
			tweetparse(tweet, '', self.db, self.classifier)
		except:
			pass

		return True
# End of "class StreamPrinter"

def main():
	app = 'firehose'

	config = ConfigParser.ConfigParser()
	if len(sys.argv) > 1:
		conf = sys.argv[1]
	else :
		conf = '%s.ini' % app

	if len(config.read(conf)) == 0:
		print "unable to read configuration file '%s'" % conf
		sys.exit(1)

	user = None
	if config.has_option(app, 'user'):
		user = config.get(app, 'user')

	if (user is None) or len(user) == 0:
		print "'user' option not specified"
		sys.exit(1)

        try:
		bayes_file = config.get(app, 'bayes')
		tokenizer = myTokenizer()
		classifier = reverend.thomas.Bayes(tokenizer)
		classifier.load(bayes_file)
        except Exception:
		classifier = None

	if config.has_option(app, 'debug') and (config.get(app, 'debug') == True or config.get(app, 'debug') == 'True'):
		tweepy.debug(True)

	logbase = None
	if config.has_option(app, 'logbase'):
		logbase = config.get(app, 'logbase')
		if (logbase == 'None') or (len(logbase) == 0):
			logbase = None

	if config.has_option(app, 'keywords'):
		keywords = config.get(app, 'keywords').replace(",", " ").split()
	else:
		keywords = []

	auth = twitter_auth(app, user, config)
	if check_login(user, auth) == False:
		sys.exit(0)

	print 'active user: ', user
	print "tracking keywords:", keywords

	twitterStream = Stream(auth, StreamPrinter())
	twitterStream.listener.src_account = user
	twitterStream.listener.classifier = classifier

	if logbase is None:
		print "no json logs"
		twitterStream.listener.data_fd = open('/dev/null', 'a')
	else:
		twitterStream.listener.data_fd = open('%s.%s.json' % (logbase, time.strftime('%Y%m%d-%H%M%S')), 'a')

	try:
		twitterStream.filter(track = keywords)
	except:
		twitterStream.disconnect()

if __name__ == '__main__':
	main()
