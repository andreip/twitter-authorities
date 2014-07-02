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

    def test_unshorten_url3(self):
        url = 'http://bit.ly/1qe93MS'
        expected_url =\
        'https://apps.facebook.com/my-polls/yqkvxg'
        actual_url = unshorten_url(url)
        self.assertEqual(expected_url, actual_url)


    def test_unshorten_url4(self):
        url = 'https://apps.facebook.com/my-polls/yqkvxg'
        actual_url = unshorten_url(url)
        self.assertEqual(url, actual_url)

    def test_unshorten_url5(self):
        url = 'https://www.betxchange.co.za/sport/tennis'
        actual_url = unshorten_url(url)
        self.assertEqual(url, actual_url)

    def test_unshorten_url_timeout(self):
        url =\
        'http://yoursportman.mobi/football_news_details.php?news_id=65v288294162Fse6291MXS56916444RFh231377718dTxKHF508710quE5580Dqx592&&s=58v1689136asJ10808BWa89708Zmu1599428ESNIFL586931nTh6438iRr74'
        try:
            actual_url = unshorten_url(url)
            self.assertEqual(url, actual_url)
        except Exception:
            self.assertFalse(True)

    def test_unshorten_url_head_error(self):
        url = 'http://ift.tt/Vld5X8'
        expected_url =\
        'https://myaccount.nytimes.com/auth/login?URI=http%3A%2F%2Fwww.nytimes.com%2Freuters%2F2014%2F06%2F24%2Fsports%2Ftennis%2F24reuters-tennis-wimbledon-halep.html%3F_r%3D5&REFUSE_COOKIE_ERROR=SHOW_ERROR'
        actual_url = unshorten_url(url)
        self.assertEqual(expected_url, actual_url)
