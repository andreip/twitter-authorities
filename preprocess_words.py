import re
import string

from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

stemmer = SnowballStemmer("english")
stopwords = open(r'stopwords.txt', 'r').read().splitlines()

def process_text(text):
    '''Returns a list of words that go through: punctuation removal,
    tokenization, lowercase, stemming.

    First remove URLs so we can apply the above easily, then add them
    back untouched.
    '''
    from constants import URL_REGEX
    # Save all URLs.
    urls = re.findall(URL_REGEX, text)
    # Remove all URLs.
    text = re.sub(URL_REGEX, '', text)

    # Replace punctuation with space so they can be easily tokenized.
    for c in string.punctuation:
        text = text.replace(c, ' ')

    # Get individual lower words out of text now.
    words = map(lambda word: word.lower(), word_tokenize(text))
    # Remove common words from english grammar.
    words = filter(not_stopword, words)
    # Keep only long enough words.
    words = filter(not_too_short, words)
    # Stem all words from body.
    words = map(stemmer.stem, words)
    # Remove duplicates.
    words, urls = list(set(words)), list(set(urls))
    return words + urls

def keep_only_letters(word):
    '''Given a string like "ana1.bbc", return "anabbc".'''
    letter = lambda c : 'a' <= c <= 'z' or 'A' <= c <= 'Z'
    return filter(letter, word)

def not_stopword(word):
    return word not in stopwords

def not_too_short(word):
    from constants import MIN_WORD_LEN
    return len(word) >= MIN_WORD_LEN
