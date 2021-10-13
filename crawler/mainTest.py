#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging
import sys

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

#gauth = GoogleAuth()
#gauth.LocalWebserverAuth()
#drive = GoogleDrive(gauth)

from mfpCrawler import crawler
import json
from collections import deque
import datetime
from databaseConnector import databaseConnector
from translate import Translator


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

db = databaseConnector.SqliteConnector('databaseConnector/mfp.db')
x = db.get_user_statistics()
statistics = db.get_user_statistics()
logging.info("Statistics: Found User: %i, Crawled Profiles: %i, Public Diaries: %i, Rate %.2f",
             statistics['total'], statistics['profile-crawled'], statistics['public-diary'],
             statistics['public-diary'] / statistics['profile-crawled'])
secret_config = json.loads(f.read())
y = crawler.MyFitnessPalCrawler(secret_config["email"], secret_config["password"])
to_date = datetime.date(2020, 5, 14)
x = y.crawl_friends('rynshermy')
print(x)
x = y.crawl_profile('Crossfitdad71')
print(x)
x = y.crawl_profile('Theo166')
print(x)
from_date = to_date - datetime.timedelta(days=365)
z,_ = y.crawl_diary('clemrn73', from_date, to_date)
#datetime.date(2020,2,6) min datetime.date(2019,1,1)


z = db.get_meal_item('test2')
x = db.get_uncrawled_friends_users()

username = "Theo166"
to_date = datetime.date(2021, 10, 1)
from_date = to_date - datetime.timedelta(days=365)
diary = y.crawl_diary(username, from_date, to_date)

print("hh")
