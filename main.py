#!/usr/bin/env python

from collections import defaultdict
import pprint
import re
import sys
import time

from bson.objectid import ObjectId
import pymongo

from constants import *
from helpers.helpers import similarity_score, iterator_get_next
from helpers.mongo import followers_col, friends_col
from patch_tweepy import *

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

def get_tweets(screen_name, col):
    '''Try retrieving the tweets from db if we've got all of them.
    Otherwise just do an API call.
    '''
    print 'Fetching and storing tweets for user ' + screen_name +\
          ' in collection ' + col

    # See if we've got all tweets or not.
    user = get_user(screen_name)
    tweets = db[col].find({'user.screen_name': screen_name}).sort('id',
        pymongo.ASCENDING)

    max_id = None
    # Case when we already have everything in db.
    if tweets.count() == user['statuses_count']:
        print 'Already in db, skip fetch.'
        return tweets
    # We already have some in DB, so we need not fetch everything.
    # Continue from where we left off.
    elif tweets.count():
        # Find the minimum id, that's the point where we got rate limited.
        max_id = tweets[0]['id']

    cursor = tweepy.Cursor(api.user_timeline, screen_name=screen_name,
                           max_id=max_id)
    for tweet in cursor.items():
        db[col].update({'id': tweet['id']}, tweet, upsert=True)
    print 'Done fetching and storing!'
    return db[col].find({'user.screen_name': screen_name})

def get_tweet_type(col, tweet_id):
    cursor = db[col].find({'id': tweet_id})
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

def conversation_started_by_user(col, tweet):
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
    reply_to_type = get_tweet_type(col, tweet['in_reply_to_status_id'])
    return reply_to_type != TweetType.CT

def get_retweeters(col, screen_name):
    '''Search db for patterns like RT @screen_name: and count
    the number of users.
    '''
    users = db[col].find({'text': {"$regex" : '.*RT @' + screen_name + '.*'}},
                         {'user.screen_name': 1})
    return map(lambda u: u['user']['screen_name'], users)

def compute_user_metrics_from_own_tweets(screen_name, col, author_tweets,
                                         user_metrics):
    tweets = db[col].find({'user.screen_name': screen_name}).sort('id',
                          pymongo.ASCENDING)
    retweeters, users_mentioned = [], []
    original_texts = []
    actual_retweeters = 0

    for tweet in author_tweets:
        tweet_type = get_tweet_type_from_text(tweet['text'])
        user_metrics[tweet_type] += 1
        # Find out if conversation was started by crt user.
        if tweet_type == TweetType.CT:
            user_metrics[UserMetrics.CT1] += 1
            if conversation_started_by_user(col, tweet):
                user_metrics[UserMetrics.CT2] += 1
        elif tweet_type == TweetType.OT:
            user_metrics[UserMetrics.OT1] += 1
            # Count the number of URLs one shares in his tweets.
            user_metrics[UserMetrics.OT2] += len(tweet['entities']['urls'])

            # Mark the fact that this tweet has been retweeted at least once.
            if tweet['retweet_count'] > 0:
                user_metrics[UserMetrics.RT2] += 1
            actual_retweeters += tweet['retweet_count']

            # For each original tweet, check if it's got any mentions of other
            # users.
            for user_mention in tweet['entities']['user_mentions']:
                users_mentioned.append(user_mention['screen_name'])

            # Count how many hashtags one has used in all the tweets.
            for hashtag in tweet['entities']['hashtags']:
                user_metrics[UserMetrics.OT4] += 1
            original_texts.append(tweet['text'])

    # Find in db all the authors that retweeted a given user.
    retweeters = get_retweeters(col, screen_name)
    print 'Retweeters found, actual: ', len(retweeters), actual_retweeters
    # Update the number of unique users that retweeted current users's tweets.
    user_metrics[UserMetrics.RT3] = len(set(retweeters))
    # Count the nr of users mentioned by the author; and also unique.
    user_metrics[UserMetrics.M1] = len(users_mentioned)
    user_metrics[UserMetrics.M2] = len(set(users_mentioned))

    # Computing the OT3 score on the author's tweets. See repo
    # paper IdentifyingTopicalAuthoritiesInMicroblogs.pdf for details.
    score = similarity_score(original_texts)
    user_metrics[UserMetrics.OT3] = score

def compute_user_metrics_from_other_tweets(screen_name, col, user_metrics):
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

def compute_user_metrics(screen_name, col, author_tweets):
    user_metrics = defaultdict(int)
    # Based on author's tweets.
    compute_user_metrics_from_own_tweets(screen_name, col, author_tweets,
                                         user_metrics)
    # Based on what others are saying about author.

    #TODO: fix M3,M4 metrics
    #compute_user_metrics_from_other_tweets(screen_name, col, user_metrics)

    print 'Type summary for user ' + screen_name + ': ' + str(user_metrics)
    return user_metrics


def compute_user_features(screen_name, col, author_tweets):
    '''Compute the feature list based on some metrics for each author. See
    IdentifyingTopicalAuthoritiesInMicroblogs.pdf paper for details.

    TS - Topical Signal

    '''
    metrics = compute_user_metrics(screen_name, col, author_tweets)


def find_authorities(q, col):
    '''Finds authorities for a given search.'''
    # Get a list of users that we need to consider as potential authorities
    # about the given topic (from collection col).
    for name in get_usernames(col):
        tweets = db[col].find({'user.screen_name':  name})
        features = compute_user_features(name, col, tweets)
        #print 'Features', features


def fetch_tweets(q, pages, col, lang='en', rpp=100):
    print 'Fetch tweets', q, pages, col
    page_count = 0
    for tweets in tweepy.Cursor(api2.search, q=q, lang=lang, rpp=rpp).pages():
        db[col].insert(map(lambda tweet: tweet.raw, tweets))
        page_count += 1
        if page_count >= pages:
            print 'stop after fetching page',page_count
            break
        if page_count % 10 == 0:
            print 'Fetched pages', page_count
        # Avoid rate limit.
        time.sleep(5)
    print 'Done.'


def fetch_followers_and_friends(col, user_names):
    '''Fetch follower/friends for all distinct users present in
    the db and store them in database.
    Do this in a way we don't get rate limited too, once every minute
    per query page.
    '''
    print 'Fetching friend/followers for ' + str(len(user_names)) + ' users'
    for name in user_names:
        friends_ids = []
        followers_ids = []

        friends_cursor = tweepy.Cursor(api.friends_ids, screen_name=name).pages()
        followers_cursor = tweepy.Cursor(api.followers_ids, screen_name=name).pages()
        have_friends, have_followers = True, True

        while have_friends or have_followers:
            print 'Fetching friends, followers for user ' + name
            # Get both friends,followers and then sleep so to avoid
            # rate limit.
            if have_friends:
                page = iterator_get_next(friends_cursor)
                if page:
                    friends_ids += page['ids']
                if not page or len(page['ids']) < 5000:
                    have_friends = False
            if have_followers:
                page = iterator_get_next(followers_cursor)
                if page:
                    followers_ids += page['ids']
                if not page or len(page['ids']) < 5000:
                    have_followers = False
            time.sleep(60)
        db[friends_col(col)].update({'name': name},
                                   {'name': name, 'ids': friends_ids},
                                   upsert=True)
        db[followers_col(col)].update({'name': name},
                                     {'name': name, 'ids': followers_ids},
                                     upsert=True)


def get_usernames(col):
    '''Returns a list of users (strings) from collection that:
       - wrote at least MIN_TWEETS_USER about the topic (we assume that
         the collection holds data about only one given topic)
       - does not have more than MAX_FRIENDS and MAX_FOLLOWERS, as
         we need to get that list for some feathres and it's too time expensive
         for now (twitter rate limit)
    '''
    # http://docs.mongodb.org/manual/tutorial/aggregation-zip-code-data-set/
    user_names = db[col].aggregate([
                    {"$group": {"_id": "$user.screen_name",
                                "total": {"$sum": 1}}},
                    {"$match": {"total" : {"$gte": MIN_TWEETS_USER}}}
                 ])
    user_names = map(lambda u: u['_id'], user_names['result'])
    result = []

    # Now filter those which have too many friends/followers.
    for name in user_names:
        user = db[col].find_one({"user.screen_name": name}, {"user":1})
        friends_count = user['user']['friends_count']
        followers_count = user['user']['followers_count']
        if friends_count < MAX_FRIENDS and followers_count < MAX_FOLLOWERS:
            result.append(name)
        else:
            print 'Skipping user ' + name + ' with friends,followers: ',\
                  friends_count, followers_count
    print 'Users for which to fetch friends/followers', result
    return result


def exit():
    print 'Call like: ' + sys.argv[0] +\
          ' [fetch search pages][stats][compute search]'
    sys.exit(1)


def main():
    if len(sys.argv) == 1:
        exit()
    # Fetch and store from twitter to db.
    if sys.argv[1] == 'fetch':
        assert len(sys.argv) == 4
        col = search = sys.argv[2]
        pages = int(sys.argv[3])
        # Save tweets for a given query in the collection with same name
        # for simplicity and consistency.
        fetch_tweets(search, pages, col)

        # Find the users that have at least MIN_TWEETS_USER tweets in our db.
        # Also discard those with too many followers/friends.
        user_names = get_usernames(col)
        fetch_followers_and_friends(col, user_names)
    # Compute authorities by inspecting db.
    elif sys.argv[1] == 'compute':
        assert len(sys.argv) == 3
        col = search = sys.argv[2]
        find_authorities(search, col)
    # See rate limit info.
    elif sys.argv[1] == 'stats':
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(api.rate_limit_status())
    else:
        exit()

if __name__ == '__main__':
    main()
