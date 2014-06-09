from collections import defaultdict
import re

from bson.objectid import ObjectId
import pymongo
import tweepy

from constants import *

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
# This one is to avoid a bug with tweepy once you add jsonParser to it.
# https://github.com/tweepy/tweepy/issues/370
api2 = tweepy.API(auth)

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

def get_tweet_type(tweet_id, col=COLLECTION):
    cursor = db[COLLECTION].find({'id': tweet_id})
    if cursor.count() > 0:
        tweet = cursor.next()
    else:
        print 'Fetching tweet id ' + str(tweet_id)
        tweet = api.get_status(tweet_id)
        db[col].update({'id': tweet['id']}, tweet, upsert=True)
    return get_tweet_type_from_text(tweet['text'])

def get_tweet_type_from_text(tweet_text):
    '''Based on the text it can return one of these types:
     - original tweet OT
     - conversational tweet CT
     - repeated tweet RT
    '''
    if re.match('^@\w+.*', tweet_text):
        return TweetType.CT
    if re.match('^RT @\w+:.*', tweet_text):
        return TweetType.RT
    return TweetType.OT

def conversation_started_by_user(tweet):
    '''Check if a tweet like "@john how are you man" is
    first started by john first or by the author itself.
    '''
    # If it's not an in reply to conversation, then he just wanted to
    # talk with @username, he started it :).
    if not tweet['in_reply_to_status_id']:
        return True
    # Else it's still a possibility that he replied to a non
    # conversational tweet (!= CT), in which case he yet again
    # started the discussion.
    reply_to_type = get_tweet_type(tweet['in_reply_to_status_id'])
    return reply_to_type != TweetType.CT

def compute_user_stats_from_own_tweets(screen_name, user_metrics,
                                       col=COLLECTION):
    tweets = get_tweets(screen_name, col)
    retweeters, users_mentioned = [], []

    for tweet in tweets:
        tweet_type = get_tweet_type_from_text(tweet['text'])
        user_metrics[tweet_type] += 1
        # Find out if conversation was started by crt user.
        if tweet_type == TweetType.CT:
            if conversation_started_by_user(tweet):
                 user_metrics[UserMetrics.CT2] += 1
        elif tweet_type == TweetType.OT:
            # Mark the fact that this tweet has been retweeted at least once.
            if tweet['retweet_count'] > 0:
                user_metrics[UserMetrics.RT2] += 1
                # Keep a record of all the users that retweeded author's
                # tweets. This way we can compute the nr of unique retweeters.
                retweeters += map(lambda x: x['user']['screen_name'],
                                  api.retweets(tweet['id']))
            # For each original tweet, check if it's got any mentions of other
            # users.
            for user_mention in tweet['entities']['user_mentions']:
                users_mentioned.append(user_mention['screen_name'])

    # Update the number of unique users that retweeted current users's tweets.
    user_metrics[UserMetrics.RT3] = len(set(retweeters))
    # Count the nr of users mentioned by the author; and also unique.
    user_metrics[UserMetrics.M1] = len(users_mentioned)
    user_metrics[UserMetrics.M2] = len(set(users_mentioned))

def compute_user_stats_from_other_tweets(screen_name, user_metrics,
                                         col=COLLECTION):
    '''Find tweets that mention the author. These we'll not keep
    in the db for simplicity. The tactic here would be to (for future #TODO):
     * gather everythong and store in DB
     * make api calls only for those with since_id > the biggest id we could
       find in our DB matching @screen_name.

    But for now, just do an api call all the time.
    '''
    users_mentioning_author = []
    # Get all the authors that mention "@screen_name" by using search API.
    # We actually also have to check so those are no CT (conversational type);
    # as it turns out the API is inexact and also brings some CTs. Moreover,
    # it does not return all mentions :(, but will have to
    # do as I've found no better option.
    tweets = tweepy.Cursor(api2.search, q="@" + screen_name, rpp=100).items()
    for tweet in tweets:
        tweet_type = get_tweet_type_from_text(tweet.text)
        if tweet_type == TweetType.OT:
            users_mentioning_author.append(tweet.user.screen_name)
    user_metrics[UserMetrics.M3] = len(users_mentioning_author)
    user_metrics[UserMetrics.M4] = len(set(users_mentioning_author))

def compute_user_stats(screen_name, col=COLLECTION):
    user_metrics = defaultdict(int)
    # Based on author's tweets.
    compute_user_stats_from_own_tweets(screen_name, user_metrics)
    # Based on what others are saying about author.
    compute_user_stats_from_other_tweets(screen_name, user_metrics)

    print 'Type summary for user ' + screen_name + ': ' + str(user_metrics)

compute_user_stats('mishu21')
#compute_user_stats('anpetre')
