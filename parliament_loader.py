#!/usr/bin/env python
# vim: tabstop=4:softtabstop=4:shiftwidth=4:noexpandtab:

import json
import sys
import os
import re
import hashlib
import time
import datetime
import dateutil.parser
import pymongo as pm
import argparse
import logging

def log_config(lvl):
	logging_format = '%(levelname)s: %(message)s'
	if lvl > 1:
		logging.basicConfig(format=logging_format, level=logging.DEBUG)
	elif lvl > 0:
		logging.basicConfig(format=logging_format, level=logging.INFO)
	else:
		logging.basicConfig(format=logging_format, level=logging.WARN)

def dbConnect(db='mongodb://localhost:27017/', check_index=True):
	'''connect to database, and optionally verify the indexes'''
	mc = pm.MongoClient(db)
	mc['admin'].command('setParameter', textSearchEnabled=True) #enable FTS
	dbh = mc['parliament']

	if check_index is True:
		print "checking indexes"
		tweets_table = dbh['tweets']
		tweets_table.ensure_index( [('id',pm.ASCENDING)], unique=True, drop_dups=True)
		tweets_table.ensure_index([('created_at', pm.ASCENDING)])
		tweets_table.ensure_index([('timestamp_ms', pm.ASCENDING)])

		users_table = dbh['users']
		users_table.ensure_index( [('id',pm.ASCENDING)], unique=True, drop_dups=True)
		users_table.ensure_index( [('screen_name', pm.ASCENDING)] )
		users_table.ensure_index('name')

	return dbh

def tweetfix(t):
	if 'timestamp_ms' in t:
		t['timestamp_ms'] = int(t['timestamp_ms'])
	if 'created_at' in t:
		t['created_at'] = dateutil.parser.parse(t['created_at'])

def userfix(u):
	u['id'] = int(u['id'])
	u['created_at'] = dateutil.parser.parse(u['created_at'])
	for k in [ 'notifications', 'friends_count', 'followers_count', 'favourites_count', 'listed_count', 'statuses_count', 'is_translator', 'is_translation_enabled', 'follow_request_sent', 'profile_link_color', 'profile_text_color', 'profile_background_color', 'profile_sidebar_border_color', 'profile_sidebar_fill_color' ] :
		try:
			u.pop(k, None)
		except KeyError:
			logging.debug("userfix key error", k)
			pass

def main():
	descr = 'Load tweets from streamlog into the database'
	parser = argparse.ArgumentParser(description=descr, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-v', '--verbose', dest='verbose', action='count', default=False, help='increase verbosity')
	parser.add_argument('-m', '--mongodb', dest='db', metavar='MONGO', default='mongodb://localhost:27017/', help='server url')
	parser.add_argument(dest='files', metavar='FILE', nargs='+', default=None, help='streamlog FILE(S)')
	args = parser.parse_args()
	log_config(args.verbose)

	if len(args.files) == 0:
		logging.error("no files specified")
		sys.exit(1)

	'''do all the things!'''
	dbh = dbConnect(args.db)

	for jfile in args.files:
		with open(jfile, 'r') as fh:
			logging.info('processing ' + jfile)
			got_eof = False
			nr = 0
			nl = 0
			while got_eof is False:
				l = fh.readline()
				nl += 1
				if len(l):
					try:
						tweetobj = json.loads(l)
						userobj = tweetobj.pop('user', None)
						userfix(userobj)
						tweetfix(tweetobj)
						uid = userobj['id']
						tweetobj['user'] = uid
						dbh['tweets'].insert(tweetobj)
						dbh['users'].update({'id': uid}, {'$set': userobj}, upsert=True )
						nr += 1
					except TypeError, e:
						logging.debug("TypeError:" + str(e))
						pass # probably thrown when we don't have a uid for this tweet
					except KeyError, e:
						logging.debug("KeyError:" + str(e))
						pass
					except ValueError, e:
						logging.debug("ValueError:" + str(e))
						pass # not doing anything about mangled json
					except pm.errors.DuplicateKeyError:
						pass # ignore duplicate inserts
					except KeyboardInterrupt:
						logging.error('Caught ^C, exiting.')
						logging.info('loaded %d tweets', nr)
						sys.exit(0)
				else:
					got_eof = True

				if (nr > 0) and (nr % 1000 == 0):
					logging.info("progress: %d", nr)
			logging.info('processed %d lines', nl)

if __name__ == '__main__':
	main()
