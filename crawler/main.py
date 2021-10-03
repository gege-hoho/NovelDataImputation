#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging

from mfpCrawler.crawler import MyFitnessPalCrawler
import json
from collections import deque
import datetime
from databaseConnector.databaseConnector import SqliteConnector

# read the secrets from file

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.FileHandler("../debug.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.INFO)
f = open("secret.json", 'r')
secret_config = json.loads(f.read())
crawler = MyFitnessPalCrawler(secret_config["email"], secret_config["password"])
db = SqliteConnector('databaseConnector/mfp.db')

queue = deque()
# while True:
for i in range(500):
    if len(queue) == 0:
        # no more users in queue get more from db
        uncrawled_users = db.get_uncrawled_friends_users()
        if len(uncrawled_users) == 0:
            logging.info("No more uncrawled users. Abort...")
            break
        logging.info("Requested %i uncrawled users from DB", len(uncrawled_users))
        queue.extend(uncrawled_users)
    curr_user = queue.popleft()

    # crawl profile information
    user_data = crawler.crawl_profile(curr_user.username)
    curr_user.gender = user_data['gender']
    curr_user.location = user_data['location']
    curr_user.has_public_diary = user_data['has_public_diary']
    curr_user.joined_date = user_data['joined']
    curr_user.profile_crawl_time = datetime.datetime.now()

    # crawl friends
    friends = crawler.crawl_friends(curr_user.username)

    curr_user.friends_crawl_time = datetime.datetime.now()
    db.save_user(curr_user)

    db.create_users(friends)
