from helpers import get_config

config = get_config()

CONSUMER_KEY = config.get('credentials', 'CONSUMER_KEY')
CONSUMER_SECRET = config.get('credentials', 'CONSUMER_SECRET')
ACCESS_TOKEN = config.get('credentials', 'ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = config.get('credentials', 'ACCESS_TOKEN_SECRET')

class TweetType:
    '''Tweet Types:
     - original tweet OT
     - conversational tweet CT
     - repeated tweet RT
    '''
    OT, CT, RT = range(3)

class UserMetrics:
    '''Type of metrics for each authority:
     * OT1 - Number of original tweets
     * OT2 - Number of links shared
     * OT3 - Self-similarity score that computes how similar is
             author's recent tweet w.r.t her previous tweets
     * OT4 - Number of keyword hashtags used
     * CT1 - Number of conversational tweets
     * CT2 - Number of conversational tweets where conver-
             sation is initiated by the author
     * RT1 - Number of retweets of other's tweet
     * RT2 - Number of unique tweets (OT1) retweeted by other users
     * RT3 - Number of unique users who retweeted author's tweets
     * M1  - Number of mentions of other users by the author
     * M2  - Number of unique users mentioned by the author
     * M3  - Number of mentions by others of the author
     * M4  - Number of unique users mentioning the author
    '''
    OT1, CT1, RT1 = TweetType.OT, TweetType.CT, TweetType.RT
    OT2, CT2, RT2, RT3 = range(3, 7)
    M1, M2, M3, M4 = range(7, 11)
    OT3, OT4 = range(11, 13)

# Minimum number of tweets a user must have in order to be
# considered as potential authority in algorithm.
MIN_TWEETS_USER = 10

# MongoDB specifics.

SAMPLE_COLLECTION = 'tweets_en'
COLLECTION = 'tweets_test'
COLLECTION_USERS = 'tweets_users'

DATABASE_NAME = 'licenta'
