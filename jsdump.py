#!/usr/bin/env python

import os
import sys
import json
from parliament_utils import *
import reverend.thomas
from optparse import OptionParser

def main():
	parser = OptionParser()
	parser.add_option( "-b", "--bayesfile", dest="bayesfile", default=None, help="FILE to operate on.", metavar="FILE")
	parser.add_option( "-d", "--dedup", dest="dedup", default=False, action="store_true", help="suppress excessively similar tweets")
	(options, args) = parser.parse_args()

	dedup = None
	if options.dedup:
		dedup = {'None': True}

	classifier = None
	if options.bayesfile:
		tokenizer = myTokenizer()
		classifier = reverend.thomas.Bayes(tokenizer)
		try:
			classifier.load(options.bayesfile)
		except IOError:
			print "INFO: unable to load bayes file '%s'" % options.bayesfile
			pass

	for f in args :
		fd = open(f, 'r')
		for js in fd.readlines() :
			tweet = json.loads(js)
			if 'text' not in tweet:
				continue # can't classify non-text tweets

			tweetparse(tweet, classifier=classifier, dedup=dedup)
		fd.close()

if __name__ == '__main__':
	main()
