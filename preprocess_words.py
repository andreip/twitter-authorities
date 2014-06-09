import re
import string

from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize

MIN_WORD_LEN = 3

stemmer = SnowballStemmer("english")
stopwords = open(r'stopwords.txt', 'r').read().splitlines()

def process_text(text):
    '''Returns a list of words that go through: punctuation removal,
    tokenization, lowercase, stemming and removal of URLs.'''
    # Remove all URLs.
    text = re.sub(r'https?:\/\/[^\s\r\n\t]+', '', text)

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
    words = list(set(words))
    return words

def keep_only_letters(word):
    '''Given a string like "ana1.bbc", return "anabbc".'''
    letter = lambda c : 'a' <= c <= 'z' or 'A' <= c <= 'Z'
    return filter(letter, word)

def not_stopword(word):
    return word not in stopwords

def not_too_short(word):
    return len(word) >= MIN_WORD_LEN
