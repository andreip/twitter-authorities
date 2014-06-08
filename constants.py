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

# MongoDB specifics.

SAMPLE_COLLECTION = 'tweets_en'
COLLECTION = 'tweets_test'
COLLECTION_USERS = 'tweets_users'

DATABASE_NAME = 'licenta'
