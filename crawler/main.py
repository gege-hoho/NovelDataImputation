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
from databaseConnector.databaseConnector import SqliteConnector, database_date_format, database_date_time_format

# read the secrets from file

mode_friends = 'friends'
mode_diaries = 'diaries'

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                    datefmt=database_date_time_format,
                    handlers=[
                        logging.FileHandler("../debug.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.INFO)


def read_json(filename):
    f = open(filename, 'r')
    config = json.loads(f.read())
    f.close()
    return config


def check_config_integrity(config):
    """
    Checks if the config is as expected
    :param config: config object
    :type config: dict
    """
    if not config['mode'] in (mode_friends, mode_diaries):
        raise Exception(f"mode {config['mode']} is not known")


def check_secret_config_integrity(config):
    """
    Checks if the config is as expected
    :param config: config object
    :type config: dict
    """
    if not (config['email'] and config['password'] and config['username']):
        raise Exception('some values in secret config are missing')


def main():
    secret_config = read_json("secret.json")
    check_secret_config_integrity(secret_config)

    config = read_json("config.json")
    check_config_integrity(config)

    crawler = MyFitnessPalCrawler(secret_config["email"], secret_config["password"])
    db = SqliteConnector('databaseConnector/mfp.db')
    mode = config['mode']
    logging.info("Starting with mode %s", mode)
    queue = deque()
    while True:
        if len(queue) == 0:
            # no more users in queue get more from db
            uncrawled_users = []
            if mode == mode_friends:
                uncrawled_users = db.get_uncrawled_friends_users()
            if mode == mode_diaries:
                uncrawled_users = db.get_uncrawled_diaries_users()

            if len(uncrawled_users) == 0:
                logging.info("No more uncrawled users. Abort...")
                break
            logging.info("Requested %i uncrawled users from DB", len(uncrawled_users))
            queue.extend(uncrawled_users)
        curr_user = queue.popleft()

        if mode == mode_friends:
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
        if mode == mode_diaries:
            max_date = datetime.date(2021, 10, 1)
            from_date = curr_user.joined_date
            if not from_date:
                logging.info("%s has no joined date, last 5 years are crawled", curr_user.username)
                from_date = max_date - datetime.timedelta(days=365 * 5)
            to_date = from_date + datetime.timedelta(days=365)

            diary = []
            while from_date < max_date:
                logging.info("crawl between %s, %s", from_date.strftime(database_date_format),
                             to_date.strftime(database_date_format))
                curr_diary = crawler.crawl_diary(curr_user.username, from_date, to_date)
                # update time
                from_date = to_date
                to_date = from_date + datetime.timedelta(days=365)
                if to_date > max_date:
                    to_date = max_date
                diary.extend(curr_diary)

            logging.info("crawled diaries of %s", curr_user.username)


if __name__ == '__main__':
    main()
