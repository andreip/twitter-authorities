from helpers.helpers import unshorten_url

def migrate_urls(db, col):
    '''Expand the URLs as much as possible and update it back, upsert.'''
    cursor = db[col].find({'entities.urls.expanded_url': {'$exists': True}})
    total = cursor.count()
    print 'Total urls to go', total
    for i, tweet in enumerate(cursor):
        for url in tweet['entities']['urls']:
            u = url['expanded_url']
            print u
            uu = unshorten_url(u)
            url['expanded_url'] = uu
            print uu
        db[col].update({'_id': tweet['_id']}, tweet, upsert=True)
        if (i+1) % 100 == 0:
            print '---------------'
            print 'At migration step ' + str(i) + ' / ' + str(total)
            print '---------------'
