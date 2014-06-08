from collections import defaultdict
import re

from bson.objectid import ObjectId
import pymongo
import tweepy

from constants import *

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

conn = pymongo.MongoClient("mongodb://localhost")
db = conn[DATABASE_NAME]

## Show rate limit info
#print api.rate_limit_status()

## Find a tweet
#tweet = db.tweets_test.find_one({"id" : 400009508526632960})

## Search tweets for query and save them in mongo
#public_tweets = tweepy.Cursor(api.search, q="roland garros", lang='en',rpp=100).items(2000)
#for tweet in public_tweets:
#    print tweet.text
#    #db.tweets_en.update({'id': tweet.raw['id']}, tweet.raw, upsert=True)

## Gather user's tweets
#public_tweets = tweepy.Cursor(api.user_timeline, screen_name='mishu21').items(200)
#for tweet in public_tweets:
#    print tweet.text, tweet.id
#    #db.tweets_en.update({'id': tweet.raw['id']}, tweet.raw, upsert=True)
#    db.tweets_test.update({'id': tweet.raw['id']}, tweet.raw, upsert=True)

#def get_user_stats(screen_name):
#    public_tweets = tweepy.Cursor(api.user_timeline, screen_name='anpetre')

def get_user(screen_name, cached=True, col=COLLECTION_USERS):
    '''In case cached=True try retrieving the user from db.
    In case it's not possible, do API call.
    '''
    if cached:
        cursor = db[col].find({'screen_name': screen_name})
        if cursor.count() > 0:
            return cursor.next()

    # Fetch and store.
    user = api.get_user(screen_name=screen_name)
    db[col].insert(user)
    return user

def get_tweets(screen_name, col=COLLECTION):
    '''Try retrieving the tweets from db if we've got all of them.
    Otherwise just do an API call.
    '''
    print 'Fetching and storing tweets for user ' + screen_name +\
          ' in collection ' + col

    # See if we've got all tweets or not.
    user = get_user(screen_name)
    tweets = db[col].find({'user.screen_name': screen_name})

    # Case when we already have everything in db.
    if tweets.count() == user['statuses_count']:
        print 'Already in db, skip fetch.'
        return tweets

    cursor = tweepy.Cursor(api.user_timeline, screen_name=screen_name)
    for tweet in cursor.items():
        db[col].update({'id': tweet['id']}, tweet, upsert=True)
    print 'Done fetching and storing!'
    return db[col].find({'user.screen_name': screen_name})

def get_tweet_type(tweet_id):
    cursor = db[COLLECTION].find({'id': tweet_id})
    if cursor.count() > 0:
        tweet = cursor.next()
    else:
        print 'Fetching tweet id ' + str(tweet_id)
        tweet = api.get_status(tweet_id)
    return get_tweet_type_from_text(tweet['text'])

def get_tweet_type_from_text(tweet_text):
    '''Based on the text it can return one of these types:
     - original tweet OT
     - conversational tweet CT
     - repeated tweet RT
    '''
    if re.match('^@\w+.*', tweet_text):
        print tweet_text
        return TweetType.CT
    if re.match('^RT @\w+:.*', tweet_text):
        return TweetType.RT
    return TweetType.OT

def compute_user_stats(screen_name, col=COLLECTION):
    tweets = get_tweets(screen_name, col)
    print tweets.count()
    tweet_types = defaultdict(int)
    for tweet in tweets:
        tweet_type = get_tweet_type_from_text(tweet['text'])
        tweet_types[tweet_type] += 1
    print 'Type summary for user ' + screen_name + ': ' + str(tweet_types)

#compute_user_stats('mishu21')
compute_user_stats('anpetre')

