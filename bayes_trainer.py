#!/usr/bin/env python

import os
import sys
import json
import ConfigParser
import sqlite3
from parliament_utils import *
import reverend.thomas

def main():
	dat = 'bayes.dat'
	tokenizer = myTokenizer()
	classifier = reverend.thomas.Bayes(tokenizer)
	try:
		classifier.load(dat)
	except IOError:
		print "INFO: unable to load bayes file '%s'" % dat
		pass

	n = 0
	for f in sys.argv[1:] :
		print "open(%s)" % f
		fd = open(f, 'r')
		for js in fd.readlines() :
			tweet = json.loads(js)
			if 'text' not in tweet:
				continue # can't classify non-text tweets

			# "lang_%s" generates a meaningful token
			# screen_name generates a meaningful token
			text = sanitize("lang_%s lang_%s %s %s" %
				(tweet['user']['lang'], tweet['lang'],
				tweet['user']['screen_name'],
				tweet['text']) )

			interesting, confidence = is_worthy(text, classifier)
			tweetparse(tweet)
			print "interesting=%d confidence=%d%%" % (interesting, int(confidence*100))
			k = kbhit('up-/down-vote?') # returns '+0- xq'
			print ""
			if k == '+' :
				# print "train('yes')"
				classifier.train('yes', text)	
			elif k == '-' :
				# print "train('no')"
				classifier.train('no', text)
			elif k == 'x' :
				# print "forgetting..."
				classifier.untrain('yes', text)
				classifier.untrain('no', text)
			elif k == 'q' :
				classifier.save(dat)
				sys.exit(0)
			else :
				# print "no-op"
				pass

			n += 1
			if (n % 25) == 0 : # save classifier state
				classifier.save(dat)
		fd.close()
		try:
			classifier.save(dat)
		except Exception:
			print "WARN: unable to load bayes file '%s'" % dat
			pass
		print ""

if __name__ == '__main__':
	main()

