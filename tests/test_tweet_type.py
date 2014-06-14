import time

import unittest
import tweepy

from constants import *
from main import get_tweet_type_from_text, TweetType, get_user_mentions

class TestTweetType(unittest.TestCase):
    def setUp(self):
        self.rt_type = "RT @ubervu: RT @ggerik: Critical for global ..."
        self.rt_type_id = 424644245992255488
        self.ct_type = "@anpetre haha, you should ..."
        self.ct_type_id = 424670463852568576
        self.ot_type = "tweeting 11 @TED_TALKS link so I don't ..."
        self.ot_type_id = 400009508526632960

    def get_api(self):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
        return api

    def test_tweet_type_text(self):
        self.assertEqual(TweetType.OT, get_tweet_type_from_text(self.ot_type))
        self.assertEqual(TweetType.CT, get_tweet_type_from_text(self.ct_type))
        self.assertEqual(TweetType.RT, get_tweet_type_from_text(self.rt_type))

    def test_get_user_mentions(self):
        api = self.get_api()
        # RT verify mentions
        tweet = api.get_status(self.rt_type_id)
        tweet_type = get_tweet_type_from_text(tweet['text'])
        self.assertEqual(['ggerik'], get_user_mentions(tweet, tweet_type))
        # CT verify mentions
        tweet = api.get_status(self.ct_type_id)
        tweet_type = get_tweet_type_from_text(tweet['text'])
        self.assertEqual([], get_user_mentions(tweet, tweet_type))
        # OT verify mentions
        tweet = api.get_status(self.ot_type_id)
        tweet_type = get_tweet_type_from_text(tweet['text'])
        self.assertEqual(['TED_TALKS'], get_user_mentions(tweet, tweet_type))
