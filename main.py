#!/usr/bin/env python

from collections import defaultdict
import math
import pprint
import re
import sys
import time

import matplotlib
matplotlib.use('TkAgg')

import numpy as np
import pylab as pl
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale

from bson.objectid import ObjectId
import pymongo

from constants import *
from helpers.helpers import similarity_score, iterator_get_next
from helpers.mongo import *
from patch_tweepy import *

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
# This one is to avoid a bug with tweepy once you add jsonParser to it.
# https://github.com/tweepy/tweepy/issues/370
api2 = tweepy.API(auth)

conn = pymongo.MongoClient("mongodb://localhost")
db = conn[DATABASE_NAME]

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
        time.sleep(5)
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

def get_user_mentions(tweet, tweet_type):
    '''Get accurate mentions by ignoring semantic header.
    * 'RT @user: The awesome news' becomes 'The awesome news'
      because RT @user is added automatically
    * '@google how awesome is your post!' -> removes '@google' from the start
      the '@google' part is added by twitter automatically if you reply
      to the post
    * '@yale, I like how you've been doing lately!'
      this is not a reply to a specific post, it's thus a mention, we
      don't strip @yale from beginning
    '''
    ignore_start_indices = []
    if tweet_type == TweetType.CT and tweet['in_reply_to_status_id']:
        ignore_start_indices.append(0)
    elif tweet_type == TweetType.RT:
        index = "RT @...".index('@')
        ignore_start_indices.append(index)

    result = []
    for user_mention in tweet['entities']['user_mentions']:
        start_index_of_mention = user_mention['indices'][0]
        # Skip the mentions that we want to ignore due to semantic header
        # added by twitter automatically.
        if not start_index_of_mention in ignore_start_indices:
            result.append(user_mention['screen_name'])
    return result

def compute_user_metrics_from_own_tweets(screen_name, col, author_tweets,
                                         user_metrics):
    print 'Compute metrics for', screen_name
    tweets = db[col].find({'user.screen_name': screen_name}).sort('id',
                          pymongo.ASCENDING)
    retweeters, users_mentioned = [], []
    tweets_texts = []
    actual_retweeters = 0

    for tweet in author_tweets:
        tweet_type = get_tweet_type_from_text(tweet['text'])
        # Find out if conversation was started by crt user.
        if tweet_type == TweetType.CT:
            user_metrics[UM.CT1] += 1
            if conversation_started_by_user(col, tweet):
                user_metrics[UM.CT2] += 1
        elif tweet_type == TweetType.OT:
            user_metrics[UM.OT1] += 1
            # Count the number of URLs one shares in his tweets.
            user_metrics[UM.OT2] += len(tweet['entities']['urls'])
            # Count how many hashtags one has used in all the tweets.
            for hashtag in tweet['entities']['hashtags']:
                user_metrics[UM.OT4] += 1

            # Mark the fact that this tweet has been retweeted at least once.
            if tweet['retweet_count'] > 0:
                user_metrics[UM.RT2] += 1

        elif tweet_type == TweetType.RT:
            user_metrics[UM.RT1] += 1

        # For each tweet, check if it's got any mentions of other
        # users.
        users_mentioned += get_user_mentions(tweet, tweet_type)
        # Keep a record of all texts and check their similarity score.
        tweets_texts.append(tweet['text'])
        # Count how many users have retweeted one's tweets.
        actual_retweeters += tweet['retweet_count']

    # Find in db all the authors that retweeted a given user.
    retweeters = get_retweeters(col, screen_name)
    print 'Retweeters found, actual: ', len(retweeters), actual_retweeters
    # Update the number of unique users that retweeted current users's tweets.
    user_metrics[UM.RT3] = len(set(retweeters))
    # Count the nr of users mentioned by the author; and also unique.
    user_metrics[UM.M1] = len(users_mentioned)
    user_metrics[UM.M2] = len(set(users_mentioned))

    # Computing the OT3 score on the author's tweets. See repo
    # paper IdentifyingTopicalAuthoritiesInMicroblogs.pdf for details.
    score = similarity_score(tweets_texts)
    user_metrics[UM.OT3] = score

def compute_user_metrics_from_other_tweets(screen_name, col, user_metrics):
    '''Find tweets that mention the author. We'll search only for those
    present in db, hoping almost every mentioned has been gathered as
    it's related to the topic.
    '''
    # Get all the mentions of the @screen_name user.
    users_mentioning = db[col].find({'text':
        # Don't begin with '@screen_name'.
        {'$regex': '^(?!@' + screen_name + ')' +\
                   # Don't begin with 'RT @screen_name' either.
                   '(?!RT @' + screen_name + ')' +\
                   # Characters follow and then '@screen_name' must follow too.
                   '.+@' + screen_name + '.*'
        }},
        {'user.screen_name': 1}
    )
    users_mentioning = map(lambda u: u['user']['screen_name'], users_mentioning)
    # Exclude own mentions (it may be a user retweets someone who mentioned
    # him.
    users_mentioning = filter(lambda u: u != screen_name, users_mentioning)

    user_metrics[UM.M3] = len(users_mentioning)
    user_metrics[UM.M4] = len(set(users_mentioning))

def compute_graph_user_metrics(screen_name, col, user_metrics):
    print 'Computing topically active followers',
    followers = db[followers_col(col)].find_one({'name': screen_name})
    print 'from ' + str(len(followers['ids'])) + ' followers'
    topic_active_followers = db[col].find({'id': {'$in': followers['ids']}},
                                          {'id': 1})

    print 'Computing topically active friends',
    friends = db[friends_col(col)].find_one({'name': screen_name})
    print 'from ' + str(len(friends['ids'])) + ' friends'
    topic_active_friends = db[col].find({'id': {'$in': friends['ids']}},
                                        {'id': 1})

    user_metrics[UM.G1] = topic_active_followers.count()
    user_metrics[UM.G2] = topic_active_followers.count()

def compute_user_metrics(screen_name, col):
    metrics = db[metrics_col(col)].find_one({'_id': screen_name})
    if metrics:
        return defaultdict(int, metrics['metrics'])

    user_metrics = defaultdict(int)
    author_tweets = db[col].find({'user.screen_name':  screen_name})
    compute_user_metrics_from_own_tweets(screen_name, col, author_tweets,
                                         user_metrics)
    compute_user_metrics_from_other_tweets(screen_name, col, user_metrics)
    #TODO
    #compute_graph_user_metrics(screen_name, col, user_metrics)

    print '[' + screen_name + '] METRICS: ' + str(user_metrics)

    # Store metric in DB.
    db[metrics_col(col)].update({'_id': screen_name},
                                {'_id': screen_name, 'metrics': user_metrics},
                                upsert=True)

    return user_metrics


def compute_user_features(screen_name, col):
    '''Compute the feature list based on some metrics for each author. See
    UF class for details on features (constants specific file).
    '''
    metrics = compute_user_metrics(screen_name, col)
    features = {}

    user_tweet = db[col].find_one({'user.screen_name': screen_name})
    total_tweets = user_tweet['user']['statuses_count']

    features[UF.TS] = metrics[UM.OT1] + metrics[UM.CT1] + metrics[UM.RT1]
    features[UF.TS] /= float(total_tweets)

    features[UF.SS] = 0 if not metrics[UM.OT1]\
                        else metrics[UM.OT1] / float(metrics[UM.OT1] +
                                                     metrics[UM.RT1])

    nCS1 = 0 if not metrics[UM.OT1]\
             else metrics[UM.OT1] / float(metrics[UM.OT1] + metrics[UM.CT1])
    nCS2 = (metrics[UM.CT1] - metrics[UM.CT2]) / float(metrics[UM.CT1] + 1)
    features[UF.nCS] = nCS1 + nCS_LAMBDA * nCS2

    # Avoid doing log(0), so edge case here.
    features[UF.RI] = 0 if not metrics[UM.RT3] \
                        else metrics[UM.RT2] * math.log(metrics[UM.RT3])

    MI1 = 0 if not metrics[UM.M4] else metrics[UM.M3] * math.log(metrics[UM.M4])
    MI2 = 0 if not metrics[UM.M2] else metrics[UM.M1] * math.log(metrics[UM.M2])
    features[UF.MI] = max(MI1 - MI2, 0)

    features[UF.HR] = 0 if not metrics[UM.OT1]\
                        else metrics[UM.OT4] / float(metrics[UM.OT1])

    print '[' + screen_name + '] FEATURES: ' + str(features)
    return features


def plot_features(mapping, col):
    # Create a matrix in np format.
    names = mapping.keys()
    data = np.vstack(map(lambda m: np.array(m.values()),
                     mapping.values())).astype(np.float)
    # Now all features can all be scaled appropriately.
    data = scale(data)
    reduced_data = PCA(n_components=2).fit_transform(data)

    # Store reduced features in db {name, points} so we can the
    # find users associated to them.
    for i, name in enumerate(names):
        db[rfeatures_col(col)].update({'_id': name},
                                      {'_id': name,
                                       'rfsx': reduced_data[i][0],
                                       'rfsy': reduced_data[i][1]
                                      },
                                      upsert=True)

    pl.figure(figsize=(14, 9.5))
    pl.title('Plot Users\' Features', size=18)
    pl.scatter(reduced_data[:, 0], reduced_data[:, 1], s=10)

    pl.xlim(-2, 2)
    pl.ylim(-2, 2)
    pl.xticks(())
    pl.yticks(())
    pl.show()


def find_authorities(q, col):
    '''Finds authorities for a given search.'''
    # Get a list of users that we need to consider as potential authorities
    # about the given topic (from collection col).
    mapping = {}
    for name in get_usernames(col):
        features = compute_user_features(name, col)
        mapping[name] = features
    plot_features(mapping, col)


def fetch_tweets(q, pages, col, lang='en', rpp=100):
    print 'Fetch tweets', q, pages, col
    # Make sure db is clean.
    db[col].remove({})
    page_count = 0
    max_id = None
    while page_count < pages:
        tweets = api.search(q=q, lang=lang, count=rpp, max_id=max_id)['statuses']
        db[col].insert(tweets)
        page_count += 1
        # Update the max_id based on those fetched, as twitter returns
        # tweets in id descending order.
        max_id = tweets[-1]['id'] - 1
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
        db[friends_col(col)].update({'_id': name},
                                   {'_id': name, 'ids': friends_ids},
                                   upsert=True)
        db[followers_col(col)].update({'_id': name},
                                     {'_id': name, 'ids': followers_ids},
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
    # Compute the average number of posts for all users.
    avg = db[col].aggregate([
            {'$group': {'_id': '$user.screen_name', 'total': {'$sum': 1}}},
            {'$group': {'_id': None, 'avgNr': {'$avg': '$total'}}}
    ])['result'][0]['avgNr']
    user_names = db[col].aggregate([
                    {'$group': {'_id': '$user.screen_name',
                                'total': {'$sum': 1}}},
                    {'$match': {'total' : {'$gte': math.ceil(avg)}}}
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
