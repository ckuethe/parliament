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
import setproctitle

class StreamPrinter(StreamListener):
	def __init__(self):
		self.data_fd = None
		self.src_account = None
		self.classifier = None
		self.suppressor = None
		self.badtags = None
		self.db = None
		self.dedup = {'None': True}
		
	def on_data(self, data):
		try:
			tweet = json.loads(data)
		except Exception as e:
			return # invalid json

		if self.data_fd is not None:
			self.data_fd.write(data) # valid json, log it.

		if tweet.keys() == [u'friends']:
			return # not interested in "friends" packet

		if u'text' not in tweet:
			return # not a tweet we can handle

		hashtags = set(map(lambda x: x['text'].lower(), tweet['entities']['hashtags']))
		if self.badtags.intersection(hashtags):
			return

		if self.suppressor and re.match(self.suppressor, tweet['text']):
			return

		try:
			tweetparse(tweet, src_account='', db=self.db, classifier=self.classifier, dedup=self.dedup)
		except Exception as e:
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

	setproctitle.setproctitle(re.sub('[.]ini', '', conf))
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
		keywords = config.get(app, 'keywords').lower().replace(",", " ").split()
	else:
		keywords = []

	if config.has_option(app, 'suppressor'):
		suppressor = re.compile(unicode(config.get(app, 'suppressor')))
	else:
		suppressor = None

	if config.has_option(app, 'badtags'):
		badtags = config.get(app, 'badtags').lower().replace('#', '')
		badtags = set( re.split('\s+', badtags) )
	else:
		badtags = set('')

	auth = twitter_auth(app, user, config)
	if check_login(user, auth) == False:
		sys.exit(0)

	print 'active user: ', user
	print "tracking keywords:", keywords
	print "suppression regex:", suppressor.pattern if suppressor else 'None'
	print "suppressed hashtags:", badtags

	if logbase is None:
		print "no json logs"
		logfd = open('/dev/null', 'a')
	else:
		logfd = open('%s.%s.json' % (logbase, time.strftime('%Y%m%d-%H%M%S')), 'a')

	while True:
		try:
			twitterStream = Stream(auth, StreamPrinter())
			twitterStream.listener.src_account = user
			twitterStream.listener.classifier = classifier
			twitterStream.listener.suppressor = suppressor
			twitterStream.listener.badtags = badtags
			twitterStream.listener.data_fd = logfd

			twitterStream.filter(track = keywords)
		except KeyboardInterrupt:
			twitterStream.disconnect()
			sys.exit(0)
		except Exception as e:
			#print e
			twitterStream.disconnect()
			time.sleep(15)

if __name__ == '__main__':
	main()
