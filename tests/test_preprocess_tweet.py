import unittest
import numpy as np

from preprocess_words import process_text
from helpers.helpers import unshorten_url

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

    def test_unshorten_url(self):
        '''Test the URL is correctly unshortened by the
        used unshortener helper.
        '''
        # Keep an example of a tweet which has the expanded_url
        # also shortened, so it needs to get it expanded and
        # updated.
        url = 'http://t.co/hAplNMmSTg'
        expected_url = 'http://www.wtatennis.com/players/player/13516/title/simona-halep'
        actual_url = unshorten_url(url)
        self.assertEqual(expected_url, actual_url)

    def test_unshorten_url2(self):
        url = 'http://fb.me/23mFY1Laf'
        expected_url =\
        'https://www.youtube.com/watch?v=enG11nDzaAI&list=UUNa8NxMgSm7m4Ii9d4QGk1Q'
        actual_url = unshorten_url(url)
        self.assertEqual(expected_url, actual_url)
