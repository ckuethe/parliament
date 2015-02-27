# Parliament

Parliament is intended to help you surface more interesting content and reduce
annoyance in a busy set of twitter feeds. Having several accounts or following
active twitter users can make it easy to miss interesting content;  parliament
can help by applying various text processing techniques such as naive bayesian
filtering, clustering and scoring. It's very much a work in progress.

## General Structure

### parliament_utils.py
common utility functions

### bayes_tool.py
Low level tool for manipulating the bayes database

### bayes_trainer.py
Interactive classifier to build the bayes database

### firehose.py
Connect to twitter's firehose and display tweets from the public timeline.
Keywords may be specified, and the results may be stored to a database.

### parliament.py
Connect as a user and display their timeline. Tweets may be stored in a
database. Bayesian filtering is applied.

### retweets.py
Read a json log and emit retweet links for graph visualization

### jsdump.py
Playback a json log

### loader.py
Load a json log into a database
