#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging
import sys

from mfpCrawler import crawler
import json
from collections import deque
import datetime
from databaseConnector import databaseConnector

# read the secrets from file

x = 'January 31, 2008'
print(datetime.datetime.strptime(x, '%B %d, %Y'))

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    handlers=[
                        logging.FileHandler("../debug.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.DEBUG)
f = open("secret.json", 'r')
secret_config = json.loads(f.read())
y = crawler.MyFitnessPalCrawler(secret_config["email"], secret_config["password"])

db = databaseConnector.SqliteConnector('databaseConnector/mfp.db')
z = db.get_meal_item('test2')
x = db.get_uncrawled_friends_users()

username = "Theo166"
to_date = datetime.date(2021, 10, 1)
from_date = to_date - datetime.timedelta(days=365)
diary = y.crawl_diary(username, from_date, to_date)

print("hh")
