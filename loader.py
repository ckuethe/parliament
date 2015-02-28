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
	parser.add_option( "-d", "--database", dest="database", default=None, help="database file", metavar='FILE')
	parser.add_option( "-u", "--user", dest="user", default='.', help="user name to insert as", metavar='USER')
	parser.add_option( "-v", "--verbose", dest="quiet", default=True, action="store_false", help="print tweets during load")
	(options, args) = parser.parse_args()

	if options.database:
		db = sqlite3.connect(options.database)
	else:
		db = None

	linecounter = 0
	for f in args :
		print "open(%s)" % f
		fd = open(f, 'r')
		for js in fd :
			try:
				tweet = json.loads(js)
				tweetparse(tweet, src_account=options.user, db=db, quiet=options.quiet, dbsync=False)
			except ValueError, KeyError:
				continue
			linecounter += 1
			if (linecounter % 250) == 0:
				raw_dot()
				if db:
					db.commit()
		fd.close()
		print ""
		if db:
			db.commit()

if __name__ == '__main__':
	main()
