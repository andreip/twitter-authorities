Summary
---

Find authorities for tweeter topics. Needs to download tweets (fetching stage), then it can compute based on fetched tweets.
Requirements:
* the implementation uses mongodb to store downloaded tweets
* see requirements.txt for more, but main packages used are: pymongo, tweepy, scikit-learn, numpy, scipy

Usage
---
* first fetch all tweets related to a topic (say "ukraine gas russia")

  `./main.py fetch "ukraine gas russia" 100` tells it to fetch 100 pages x 100 per page => 10,000 tweets.
  
* after we've fetched items, we can compute authorities:

  `./main.py compute "ukraine gas russia"` should give us the main authorities by processing all tweets from mongo collection "ukraine gas russia".
