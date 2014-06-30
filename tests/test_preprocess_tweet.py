import unittest
import numpy as np

from preprocess_words import process_text
from main import preprocess_fetched_tweet

class TestPreprocessTweet(unittest.TestCase):

    def test_urls(self):
        '''Assert how URL parsing is done.'''
        tweet = 'http://t.co/faEq3DLDCI'
        self.assertEqual(1, len(process_text(tweet)))
        tweet2 = 'http://url.com http://url2.com http://url.com'
        self.assertEqual(2, len(process_text(tweet2)))

    def test_text(self):
        '''Print how it's done, don't assert anything.'''
        tweet = 'Google at annual developer conference http://t.co/faEq3DLDCI'
        print tweet
        print process_text(tweet)
        tweet2 = 'Some tweet and has som\' words'
        print tweet2
        print process_text(tweet2)

    def test_preprocess_fetched_tweet_urls(self):
        '''Test that for given tweets, their URLs are expanded to
        the maximum and overwritten.
        '''
        # Keep an example of a tweet which has the expanded_url
        # also shortened, so it needs to get it expanded and
        # updated.
        tweet = {'entities': {'urls': [{
            'expanded_url': 'http://t.co/hAplNMmSTg',
        }]}}
        expected_tweet = {'entities': {'urls': [{
            'expanded_url':
            'http://www.wtatennis.com/players/player/13516/title/simona-halep',
        }]}}

        actual_tweet = preprocess_fetched_tweet(tweet)
        self.assertEqual(expected_tweet, actual_tweet)
