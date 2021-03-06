#!/usr/bin/env python
'''Utility functions'''

import re

from pprint import PrettyPrinter
pp = PrettyPrinter()
#pp.pprint('test')

from HTMLParser import HTMLParser
from unicodedata import normalize
hp = HTMLParser()
def sanitize(x):
	'''transcode unicode and html entities to ascii approximations'''
	return hp.unescape( normalize('NFKD', u'%s' % x ).encode('ascii','ignore').replace("\n", ' ') )

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

###########################################################################
import time
from dateutil.parser import parse as time_parser
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


###########################################################################
import reverend.thomas
class myTokenizer:
	def __init__(self):
		pass

	def tokenize(self, s):
		# "rt" is not a stopword, since it may be worth filtering out retweets, but not the original tweet
		stopwords = 'a an am as at and are but can eg not now for i i\'m ie if it is in into to the this my of on our or we with you us was when what who how than then they which'.split()
		s = s.lower().encode('utf-8') # XXX sanitize() should have transcoded this to ascii...
		s = re.sub('(http|s?ftp|imap|pop3|telnet|ssh)s?:/*\S+', '', s)
		s = s.translate(None, '<>(){}[]=&!$^|+;:@,."-?')

		tokens = s.split()
		for w in stopwords:
			try:
				tokens.remove(w)
			except ValueError:
				pass

		#print "\n========================================================================"
		#print "\ntokenize(): ", tokens
		return tokens

def is_worthy(text, classifier=None):
	'''given a text string, return true if it's sufficiently interesting'''

	# stub function
	if classifier is None:
		return True, 1.0

	try:
		labels = classifier.guess(text)
		if labels[0][0] == 'yes':
			return True, labels[0][1]
		else:
			return False, labels[0][1]
	except:
		return True, 0.0 # default action if the classifier can't answer

###########################################################################
import hashlib
def tweetparse(tweet, src_account='.', db=None, classifier=None, quiet=False, dbsync=True, rtuser=None, dedup=None):
	'''core tweet parser, handles retweets and database inserts'''
	if 'retweeted_status' in tweet:
		try:
			return tweetparse(tweet[u'retweeted_status'], src_account, db, classifier, quiet, dbsync, tweet['user']['screen_name'], dedup)
		except Exception as e:
			print "failed to parse retweet:", e
			return False, 0.0

	if 'text' not in tweet:
		return False, 0.0

	t_time = tweet_time(tweet)
	t_id = tweet['id']
	t_lang = tweet['lang']
	t_txt = sanitize(tweet['text'] )
	t_src = sanitize(re.sub('<[^>]+>', '', tweet['source'])).replace(' ', '_')
	t_hash = hashlib.sha1( re.sub('https?:/*\S+', '', t_txt) ).hexdigest()

	if dedup:
		if t_id in dedup or t_hash in dedup:
			return False, 0.0
		else:
			dedup[t_id] = True
			dedup[t_hash] = True

	if '//t.co/' in t_txt:
		t_txt = urlfix(t_txt, tweet)

	u_id = tweet['user']['id']
	u_lang = tweet['user']['lang']
	u_tz = tweet['user']['time_zone']
	u_utcoff = (tweet['user']['utc_offset'] or 0) / 3600
	u_location = sanitize(tweet['user']['location'])
	u_handle = tweet['user']['screen_name']
	u_name = sanitize(tweet['user']['name'])
	u_descr = sanitize(tweet['user']['description'])

	mentions = list()
	try:
		for mention in tweet[u'entities'][u'user_mentions']:
			mentions.append('user_'+sanitize(mention['screen_name']))
	except:
		pass
	mentions = ' '.join(mentions)

	tags = list()
	try:
		for tag in tweet[u'entities'][u'hashtags']:
			tags.append('#'+sanitize(tag['text']))
	except:
		pass
	tags = ' '.join(tags)

	if rtuser:
		rttoken = "user_%s" % rtuser
	else:
		rttoken = ''
	interesting, confidence =  is_worthy("source_%s lang_%s lang_%s user_%s %s %s %s %s" % \
		(t_src, u_lang, t_lang, u_handle, t_txt, rttoken, tags, mentions), classifier)
	if (interesting * confidence) > 0.0:
		if quiet == False:
			if rtuser:
				rttoken = "<via @%s>" % rtuser
			else:
				rttoken = ''
			print "%3d%% [%s] %s <%s> %s %s" % (int(confidence*100), t_time, src_account, u_handle, t_txt, rttoken)

	# http://paulgatterdam.com/blog/?p=121
		if db is not None:
			db.execute('INSERT OR REPLACE into users (id, screen_name, name, descr, lang, time_zone, utc_offset, location) VALUES (?,?,?,?,?,?,?,?)', (u_id, u_handle, u_name, u_descr, u_lang, u_tz, u_utcoff, u_location))
			db.execute('INSERT OR REPLACE into tweets (id, timestamp, user_id, lang, src_account, text) VALUES (?,?,?,?,?,?)', (t_id, t_time, u_id, t_lang, src_account, t_txt))
			if dbsync:
				db.commit()
	return interesting, confidence

###########################################################################
import tweepy

def check_login(user, auth):
	api = tweepy.API(auth)
	if (api.me().screen_name.lower() == user.lower()):
		return True
	else:
		return False

def twitter_auth(app, user, config):
	auth = tweepy.OAuthHandler( config.get(app, 'consumer_key'), config.get(app, 'consumer_secret'))
	auth.set_access_token( config.get(user, 'key'), config.get(user, 'secret') )
	return auth

###########################################################################
import sys,tty,termios
def kbhit(promptstr=None):
	'''simple 1 character prompter'''
	if promptstr:
		print promptstr,

	while(1):
		fd = sys.stdin.fileno()
		ta = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			k = sys.stdin.read(1)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, ta)

		if k != '':
			break

	if   k in '+YyUu' : # upvote
		return '+'
	elif k in '0Hh ' : # novote
		return '0'
	elif k in '-NnDd' : # downvote
		return '-'
	elif k in 'FfXx' : # unvote
		return 'x'
	elif k in 'Qq' : # quit
		return 'q'
	else: # default behavior = "novote"
		return '0'

