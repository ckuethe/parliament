#!/usr/bin/env python

import sys
import json
from parliament_utils import sanitize

def tweetparse(tweet, dedup):
	if 'retweeted_status' in tweet:
		u_handle = sanitize(tweet['user']['screen_name']).lower()
		u_src_handle =  sanitize(tweet['retweeted_status']['user']['screen_name']).lower()
		link = '"%s" -> "%s"' % (u_src_handle, u_handle)
		if link not in dedup:
			dedup[link] = True
			print link

def main():
	for f in sys.argv[1:] :
		sys.stderr.write("# open(%s)\n" % f)
		fd = open(f, 'r')
		dedup = dict()
		for js in fd.readlines() :
			try:
				tweet = json.loads(js)
				tweetparse(tweet, dedup)
			except ValueError, KeyError:
				pass
		fd.close()
		print ""

if __name__ == '__main__':
	main()
