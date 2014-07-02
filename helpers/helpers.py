import ConfigParser
import httplib
import io
import urlparse

from preprocess_words import process_text

def get_config(config_file='config.rc'):
    '''Reads a config file and returns the instance.'''
    with open(config_file) as f:
        # Read values from config file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(f.read()))
    return config

def iterator_get_next(iterator):
    try:
        return iterator.next()
    except StopIteration:
        return None

def similarity_texts(phrase1, phrase2):
    '''Phrase input is a list of words, not a string.
    Computes
                    |s1 ^ s2|
        S(s1, s2) = --------- ; where ^ = set intersection.
                       |s1|
    '''
    intersect = set(phrase1) & set(phrase2)
    return float(len(intersect)) / len(phrase1)

def similarity_score(texts):
    '''Computing similarity between a set of texts follows this pattern:
      * considering that the texts are ordered in cronological order so that
        time[texts[i]] < time[texts[j]], forall i < j.
      * the similarity between two texts is computer as
                    |s1 ^ s2|
        S(s1, s2) = --------- ; where ^ = set intersection.
                       |s1|
        notice that this is not symmetric, so it estimates how much does
        s1 resemble a previous post, s2.
      * compute the similaity by doing a double loop through the texts
                   2 sum(i=1,n) [ sum(j=1,i-1) S(i,j) ]
        S_total = --------------------------------------
                               (n - 1) n
        -> a high value of S_total indicates the user borrows a lot of words
           from his previous posts
        -> a small value of S_total indicates the user posts on a wider swathe
           of topics or that the vocabulary is very diverse

      * In order to better do the S(s1, s2) comparation, we need to (from
        both s1 and s2):
         - tokenize and obtain words from the phrase, remove punctuation
         - lower case words
         - remove stop words
         - stem words
         - remove URLs, @mentions
    '''
    texts = filter(lambda x: len(x) > 0, map(process_text, texts))
    n = len(texts)

    # Edge case to avoid dividing by 0 when it has 0 or 1 posts.
    if n < 2:
        return 0

    s = 0
    for i in range(0,n):
        for j in range(0,i):
            s += similarity_texts(texts[i], texts[j])
    return 2 * s / float(n * (n-1))

def unshorten_url(url):
    '''URL unshortener.

    http://stackoverflow.com/questions/7153096/how-can-i-un-shorten-a-url-using-python/7153185#7153185.'''
    from constants import TIMEOUT_URL_SHORTENER
    parsed = urlparse.urlparse(url)
    h = httplib.HTTPConnection(parsed.netloc, timeout=TIMEOUT_URL_SHORTENER)
    resource = parsed.path
    if parsed.query != "":
            resource += "?" + parsed.query
    try:
        h.request('HEAD', resource)
        response = h.getresponse()
    except Exception as e:
        print e
        return url

    if response.status/100 == 3 and response.getheader('Location'):
        url_new = response.getheader('Location')
        if 'unsupported' in url_new:
            return url
        if url == url_new:
            return url
        return unshorten_url(url_new)
    else:
        return url
