#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging
from timer import Timer
from mfpCrawler.crawler import MyFitnessPalCrawler
import json
from collections import deque
import datetime
import time
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
    if not config['sleep-time']:
        raise Exception("no sleep-time defined")
    if not type(config['sleep-time']) is int:
        raise Exception(f"sleep-time has to be an int")
    if not config['database-path']:
        raise Exception("no database-path defined")
    if not type(config['database-path']) is str:
        raise Exception(f"database-path has to be an str")
    if not config['initial-users']:
        raise Exception("no initial-users' defined")
    if not type(config['initial-users']) is list:
        raise Exception(f"database-path has to be an list")

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

    timer = Timer()
    crawler = MyFitnessPalCrawler(secret_config["email"], secret_config["password"])
    db = SqliteConnector(config["database-path"])
    #initialise users
    db.create_users(config["initial-users"])

    mode = config['mode']
    logging.info("Starting with mode %s", mode)
    users_with_problems = []
    queue = deque()
    while True:
        if len(queue) == 0:
            # no more users in queue get more from db
            uncrawled_users = []
            if mode == mode_friends:
                uncrawled_users = db.get_uncrawled_friends_users()
            if mode == mode_diaries:
                uncrawled_users = db.get_uncrawled_diaries_users()
            # filter all users with problems out
            uncrawled_users = [x for x in uncrawled_users if x not in users_with_problems]
            if len(uncrawled_users) == 0:
                logging.info("No more uncrawled users. Abort...")
                break
            logging.info("Requested %i uncrawled users from DB", len(uncrawled_users))
            queue.extend(uncrawled_users)
        curr_user = queue.popleft()
        logging.info("Crawling %s", curr_user.username)
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

            # check if there is already something for the user
            number_of_saved_meal_items = db.get_number_meal_items_from_user(curr_user)
            if number_of_saved_meal_items > 0:
                logging.warning("There is already a meal history for the user,... skipping")
                users_with_problems.append(curr_user)
                continue
            while from_date < max_date:
                logging.info("crawl between %s, %s", from_date.strftime(database_date_format),
                             to_date.strftime(database_date_format))
                diary, ret = crawler.crawl_diary(curr_user.username, from_date, to_date)
                if ret == 'password':
                    # password is required skip
                    break
                if len(diary) == 1000:
                    # only 1000 elements get crawled. After that it gets cut of at the front of the list
                    # therefore if its 1000 elements crawl again from the from_date to the last crawled date
                    # there is the possibility that the earliest date is not 100% complete therefore remove it and
                    # crawl it again

                    time.sleep(config['sleep-time'])
                    min_date_entry = min(diary, key=lambda p: p['date'])
                    logging.info("over 1000 diary entries, recrawl between %s and %s",
                                 from_date.strftime(database_date_format),
                                 min_date_entry['date'].strftime(database_date_format))
                    diary.remove(
                        min_date_entry)  # maybe not crawled 100%. Therefore remove it and crawl it again in the next step
                    diary_2, ret = crawler.crawl_diary(curr_user.username, from_date, min_date_entry['date'])
                    logging.info("found additional %i entries", len(diary_2))
                    diary = diary_2 + diary
                    if len(diary_2) == 1000:
                        # no implementation so far if the addition also expand over the limit.
                        raise Exception("Not implemented for such long diaries")

                # put in database
                logging.info("crawled %i diary entries of %s", len(diary), curr_user.username)

                timer.tick()
                for diary_entry in diary:
                    item = db.get_meal_item(diary_entry['item']['name'])
                    if not item:
                        item = db.create_meal_item(diary_entry['item'])
                    db.create_meal_history(curr_user.id, item.id, diary_entry['date'], diary_entry['meal'])
                delta = timer.tock("Database write")

                if config['sleep-time'] - delta > 0:
                    time.sleep(config['sleep-time'] - delta)

                # update time
                from_date = to_date
                to_date = from_date + datetime.timedelta(days=365)
                if to_date > max_date:
                    to_date = max_date

            curr_user.food_crawl_time = datetime.datetime.now()
            db.save_user(curr_user)


if __name__ == '__main__':
    main()
