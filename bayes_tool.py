#!/usr/bin/env python

import os
import sys
from parliament_utils import *
import reverend.thomas
from optparse import OptionParser

parser = OptionParser()
parser.add_option( "-b", "--bayesfile", dest="bayesfile", default='bayes.dat', help="FILE to operate on. Required.", metavar="FILE") 
parser.add_option( "-w", "--wordlist",  dest="wordlist",  default='words.txt', help="FILE of words to train on.", metavar="FILE") 
parser.add_option( "-y", "--yes",       dest="yes",       default=False, action="store_true", help="training words are positive")
parser.add_option( "-n", "--no",        dest="no",        default=False, action="store_true", help="training words are negative")
parser.add_option( "-l", "--learn",     dest="learn",     default=False, action="store_true", help="add words to token pool")
parser.add_option( "-f", "--forget",    dest="forget",    default=False, action="store_true", help="remove words token pool")
parser.add_option( "-s", "--set",       dest="write",     default=False, action="store_true", help="set token pool to wordlist")
parser.add_option( "-d", "--dump",      dest="dump",      default=False, action="store_true", help="dump database contents. Default.")

(options, args) = parser.parse_args()
pool = None
op = None

if (options.learn + options.forget + options.dump + options.write ) == 0:
	options.dump = True
	op = 'dump'
elif (options.learn + options.forget + options.dump + options.write ) != 1:
	print "exactly one of learn, forget, write, or dump are required"
	sys.exit(1)

if (options.learn + options.forget + options.write ) == 1:
	if (options.yes + options.no ) != 1:
		print "either yes or no must be specified when learning"
		sys.exit(1)
	else:
		if options.yes:
			pool = 'yes'
		if options.no:
			pool = 'no'
		if options.learn:
			op = 'learn'
		if options.forget:
			op = 'forget'
		if options.write:
			op = 'write'

tokenizer = myTokenizer()
classifier = reverend.thomas.Bayes(tokenizer)
try:
	classifier.load(options.bayesfile)
except:
	pass

if op == 'dump':
	for pool in classifier.poolNames():
		print "pool %s\n=========" % pool
		print "\n".join(sorted(classifier.poolTokens(pool)))
	sys.exit(0)

fd = open(options.wordlist, 'r')
words = read(fd)
fd.close()

if op == 'write':
	classifier.removePool(pool)
	classifier.newPool(pool)
	classifier.train(pool, words)
elif op == 'learn':
	classifier.train(pool, words)
elif op == 'forget':
	classifier.untrain(pool, words)

try:
	classifier.save(options.bayesfile)
except Exception as e:
	print "Unable to save bayes file '%s'" % options.bayesfile
	print e
	exit(1)
