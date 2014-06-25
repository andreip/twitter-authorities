import unittest
import numpy as np

from preprocess_words import process_text

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
