import ConfigParser
import io
from preprocess_words import process_text

def get_config(config_file='config.rc'):
    '''Reads a config file and returns the instance.'''
    with open(config_file) as f:
        # Read values from config file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(f.read()))
    return config

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
    texts = map(lambda t: [t, process_text(t)], texts)
    # TODO
    for t in texts:
        print t
    return -1
