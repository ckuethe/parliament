#!/usr/bin/env python

import sys
from parliament_utils import *
import json
import sqlite3

def raw_dot():
	sys.stdout.write('.')
	sys.stdout.flush()

def main():
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option( "-d", "--database", dest="database", default='parliament.db', help="database file", metavar='FILE')
	parser.add_option( "-u", "--user", dest="user", default='.', help="user name to insert as", metavar='USER')
	(options, args) = parser.parse_args()

	db = sqlite3.connect(options.database)

	linecounter = 0
	for f in args :
		print "open(%s)" % f
		fd = open(f, 'r')
		for js in fd.readlines() :
			try:
				tweet = json.loads(js)
				tweetparse(tweet, src_account=options.user, quiet=True)
			except ValueError, KeyError:
				continue
			linecounter += 1
			if (linecounter % 250) == 0:
				raw_dot()
				db.commit()
		fd.close()
		print ""
		db.commit()

if __name__ == '__main__':
	main()
