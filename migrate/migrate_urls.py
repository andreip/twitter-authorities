from helpers.helpers import unshorten_url

def migrate_urls(db, col):
    '''Expand the URLs as much as possible and update it back, upsert.'''
    total = db[col].count()
    cursor = db[col].find({'entities.urls.expanded_url': {'$exists': True}})
    for i, tweet in enumerate(cursor):
        url = tweet['entities']['urls']['expanded_url']
        uurl = unshorten_url(url)
        #tweet['entities']['urls']['expanded_url'] = uurl
        print url
        print uurl
        break
