#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging

from mfpCrawler import crawler
import json
from collections import deque
import datetime
from databaseConnector import databaseConnector
# read the secrets from file

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.FileHandler("../debug.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.DEBUG)
f = open("secret.json", 'r')
secret_config = json.loads(f.read())
self = crawler.MyFitnessPalCrawler(secret_config["email"], secret_config["password"])

db = databaseConnector.SqliteConnector('databaseConnector/mfp.db')
x = db.get_uncrawled_friends_users()
# x.crawl_profile("Theo166")
# x.crawl_profile("PrincessLou71186")
username = "amgjb"
self.crawl_profile(username)
username = "Theo166"
to_date = datetime.date(2021, 10, 1)
from_date = to_date - datetime.timedelta(days=365)
self.crawl_diary(username, from_date, to_date)

queue = deque()
queue.append("Theo166")

crawled = []
for i in range(5):
    curr_user = queue.popleft()

    friends = self.crawl_friends(curr_user)
    profile = self.crawl_profile(curr_user)
    if profile['has_public_diary']:
        logging.info("%s has a public diary yay!", curr_user)
    crawled.append(curr_user)
    queue.extend([x for x in friends if x not in queue and x not in crawled])
    logging.info("found %i users and crawled already %i", len(queue) + len(crawled), len(crawled))
