def followers_col(col):
    return col + '_followers'

def friends_col(col):
    return col + '_friends'

def metrics_col(col):
    return col + '_metrics'

def rfeatures_col(col):
    return col + '_rfeatures'

def features_col(col):
    return col + '_features'

def get_min_max_timestamp(col, db):
    q = db[col].aggregate([{'$group': {'_id': 0, 'minA': {'$min': '$id'},
                                      'maxA': {'$max': '$id'}}}])
    r = q['result'][0]
    return r['minA'], r['maxA']
