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
     * CT1 - Number of conversational tweets
     * CT2 - Number of conversational tweets where conver-
             sation is initiated by the author
     * RT1 - Number of retweets of other's tweet
     * RT2 - Number of unique tweets (OT1) retweeted by other users
     * RT3 - Number of unique users who retweeted author's tweets
    '''
    OT1, CT1, RT1 = TweetType.OT, TweetType.CT, TweetType.RT
    OT2, CT2, RT2, RT3 = range(3,7)

# MongoDB specifics.

SAMPLE_COLLECTION = 'tweets_en'
COLLECTION = 'tweets_test'
COLLECTION_USERS = 'tweets_users'

DATABASE_NAME = 'licenta'
