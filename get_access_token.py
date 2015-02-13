#!/usr/bin/env python
#
# Copyright 2007-2013 The Python-Twitter Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ConfigParser
from requests_oauthlib import OAuth1Session

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

def get_access_token(consumer_key, consumer_secret):
    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri='oob')

    print 'Requesting temp token from Twitter'

    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError, e:
        print 'Invalid respond from Twitter requesting temp token: %s' % e
        return
    url = oauth_client.authorization_url(AUTHORIZATION_URL)

    print ''
    print 'copy the URL to your browser and retrieve the pincode to be'
    print 'used in the next step to obtaining an Authentication Token:'
    print ''
    print url
    print ''

    pincode = raw_input('Pincode? ')

    print ''
    print 'Generating and signing request for an access token'
    print ''

    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,
                                 resource_owner_key=resp.get('oauth_token'),
                                 resource_owner_secret=resp.get('oauth_token_secret'),
                                 verifier=pincode
    )
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError, e:
        print 'Invalid respond from Twitter requesting access token: %s' % e
        return None

    print 'Your Twitter Access Token key: %s' % resp.get('oauth_token')
    print '          Access Token secret: %s' % resp.get('oauth_token_secret')
    print ''
    return (resp.get('oauth_token'), resp.get('oauth_token_secret'))


def main():
    cf = 'parliament.ini'
    config = ConfigParser.ConfigParser()
    config.readfp(open(cf))

    consumer_key = config.get('General', 'consumer_key')
    consumer_secret = config.get('General', 'consumer_secret')

    (key, secret) = get_access_token(consumer_key, consumer_secret)

    if key is not None:
        import tweepy
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, secure=True)
        auth.set_access_token(key, secret)

	api = tweepy.API(auth)
        account = api.me().screen_name
        users = config.get('General', 'users') + " " + account
        config.set('General', 'users', users)
        config.add_section(account)
        config.set(account, 'key', key)
        config.set(account, 'secret', secret)

        with open(cf, 'wb') as configfile:
            config.write(configfile)
        print 'Access Tokens for %s added to configuration file "%s"' % (account, cf)

if __name__ == "__main__":
    main()
