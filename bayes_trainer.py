#!/usr/bin/env python

import os
import sys
import json
import sqlite3
from parliament_utils import *
import reverend.thomas
from optparse import OptionParser

def main():
	parser = OptionParser()
	parser.add_option( "-b", "--bayesfile", dest="bayesfile", default='bayes.dat', help="FILE to operate on. Required.", metavar="FILE") 
	(options, args) = parser.parse_args()

	tokenizer = myTokenizer()
	classifier = reverend.thomas.Bayes(tokenizer)
	try:
		classifier.load(options.bayesfile)
	except IOError:
		print "INFO: unable to load bayes file '%s'" % options.bayesfile
		pass

	n = 0
	for f in args :
		print "open(%s)" % f
		fd = open(f, 'r')
		for js in fd.readlines() :
			tweet = json.loads(js)
			if 'text' not in tweet:
				continue # can't classify non-text tweets

			# "lang_%s" generates a meaningful token
			# screen_name generates a meaningful token
			text = sanitize("lang_%s lang_%s source_%s user_%s %s" %
				(tweet['user']['lang'], tweet['lang'],
				re.sub('<[^>]+>', '', tweet['source']).replace(' ', '_'),
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
				classifier.save(options.bayesfile)
				sys.exit(0)
			else :
				# print "no-op"
				pass

			n += 1
			if (n % 25) == 0 : # save classifier state
				classifier.save(options.bayesfile)
		fd.close()
		try:
			classifier.save(options.bayesfile)
		except Exception:
			print "WARN: unable to load bayes file '%s'" % options.bayesfile
			pass
		print ""

if __name__ == '__main__':
	main()
