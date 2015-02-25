#!/usr/bin/env python
''' this is where i test all my in-line fixups'''

import os
import sys
import json
from parliament_utils import *

def main():
	for f in sys.argv[1:] :
		fd = open(f, 'r')
		for js in fd.readlines() :
			try:
				tweet = json.loads(js)
				if 'text' not in tweet:
					continue;

				tweetparse(tweet, '')
			except:
				pass

		fd.close()
		print ""

if __name__ == '__main__':
	main()

