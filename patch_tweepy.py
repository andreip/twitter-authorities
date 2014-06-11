import tweepy
import json

@classmethod
def parse(cls, api, raw):
    status = cls.first_parse(api, raw)
    setattr(status, 'raw', raw)
    return status
# Monkey patch tweepy and add raw field with initial dict.
tweepy.models.Status.first_parse = tweepy.models.Status.parse
tweepy.models.Status.parse = parse
