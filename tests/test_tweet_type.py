import unittest
from main import get_tweet_type_text, TweetType

class TestTweetType(unittest.TestCase):
    def setUp(self):
        self.rt_type = "RT @ubervu: RT @ggerik: Critical for global ..."
        self.ct_type = "@anpetre haha, you should ..."
        self.ot_type = "tweeting 11 @TED_TALKS link so I don't ..."

    def test_tweet_type_text(self):
        self.assertEqual(TweetType.OT, get_tweet_type_text(self.ot_type))
        self.assertEqual(TweetType.CT, get_tweet_type_text(self.ct_type))
        self.assertEqual(TweetType.RT, get_tweet_type_text(self.rt_type))
