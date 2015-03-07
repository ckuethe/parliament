#!/usr/bin/env python

import threading
import sqlite3
import tweepy
from tweepy.streaming import Stream, StreamListener
import json
import ConfigParser
import re
import sys
import os
from stat import *
import time
from dateutil.parser import parse as time_parser
from parliament_utils import *
import reverend.thomas

class myStreamListener(StreamListener):
	def __init__(self):
		self.data_fd = None
		self.db = None
		self.user = None
		self.classifier = None
		self.starttime = time.strftime('%Y%m%d-%H%M%S')

	def on_connect(self):
		self.data_fd = open('parliament_log.%s.%s.json' % (self.starttime, self.user), 'a')

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
			tweetparse(tweet, self.user, self.db, self.classifier)
		except:
			pass

app = 'parliament'

def stream_thread(user, config, classifier=None):
	auth = twitter_auth(app, user, config)
	if check_login(user, auth) == False:
		print "login failed: %s" % user
		sys.exit(0)


	db = sqlite3.connect(config.get(app, 'database'))
	while True:
		try:
			twitterStream = Stream(auth, myStreamListener())
			twitterStream.listener.db = db
			twitterStream.listener.user = user
			twitterStream.listener.classifier = classifier
			twitterStream.userstream()
		except (KeyboardInterrupt, SystemExit):
			twitterStream.disconnect()
			sys.exit(0)
		except Exception as e:
			# print e
			twitterStream.disconnect()
			sleep(15)


def bayes_thread(bayes_file, classifier=None):
	'''watch the bayes file for changes, and reload in-memory representation'''
	ftime = 0
	while True:
		try:
			t = os.stat(bayes_file).st_mtime
			if t > ftime:
				ftime = t
				classifier.load(bayes_file)
				print "loaded bayes database"
		except Exception:
			pass
		time.sleep(10)


def main():
	config = ConfigParser.ConfigParser()
	config.read('%s.ini' % app)

	if config.has_option(app, 'debug') and (config.get(app, 'debug') == True or config.get(app, 'debug') == 'True'):
		tweepy.debug(True)

	threads = []
	tokenizer = myTokenizer()
	classifier = reverend.thomas.Bayes(tokenizer)

	t = threading.Thread(name='bayes', target=bayes_thread, args=(config.get(app, 'bayes'), classifier,))
	threads.append(t)
	t.start()

	for user in config.get(app, 'users').replace(",", " ").split():
		t = threading.Thread(name=user, target=stream_thread, args=(user,config,classifier,))
		threads.append(t)
		t.start()

	while True:
		try:
			time.sleep(0.2)
		except (KeyboardInterrupt, SystemExit):
			for t in threads:
				t._Thread__stop()
			sys.exit(0)

if __name__ == '__main__':
	main()
