#!/usr/bin/env python

import json
import sys
import re
from HTMLParser import HTMLParser
from unicodedata import normalize

def sanitize(x):
	hp = HTMLParser()
	return hp.unescape( normalize('NFKD', u'%s' % x ).encode('ascii','ignore') )

def tweetparse(tweet):
	if 'retweeted_status' in tweet:
		u_handle = sanitize(tweet['user']['screen_name'])
		u_src_handle =  sanitize(tweet['retweeted_status']['user']['screen_name'])
		print '"%s" -- "%s"' % (u_handle, u_src_handle)

def main():
	for f in sys.argv[1:] :
		sys.stderr.write("# open(%s)\n" % f)
		fd = open(f, 'r')
		for js in fd.readlines() :
			try:
				tweet = json.loads(js)
				tweetparse(tweet)
			except ValueError, KeyError:
				pass
		fd.close()
		print ""

if __name__ == '__main__':
	main()
