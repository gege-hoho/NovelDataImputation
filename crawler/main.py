#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging
from helper.timer import Timer
from helper.configIntegrityChecker import ConfigIntegrityChecker
from mfpCrawler.crawler import MyFitnessPalCrawler
import json
from collections import deque
import datetime
import time
from databaseConnector.databaseConnector import SqliteConnector, database_date_format, database_date_time_format

# read the secrets from file

mode_friends = 'friends'
mode_diaries = 'diaries'


def check_config_integrity(config):
    """
    Checks if the config is as expected
    :param config: config object
    :type config: dict
    """
    c = ConfigIntegrityChecker(config)

    c.check_int('sleep-time')
    c.check_set('mode', (mode_friends, mode_diaries))
    c.check_str('database-path')
    c.check_list('initial-users')
    c.check_int('friend-page-limit')
    c.check_str('log-level')
    c.check_int('crawler-timeout')
    c.check_int('crawler-max-retries')


def read_json(filename):
    f = open(filename, 'r')
    config = json.loads(f.read())
    f.close()
    return config


def check_secret_config_integrity(config):
    """
    Checks if the config is as expected
    :param config: config object
    :type config: dict
    """
    if not (config['email'] and config['password'] and config['username']):
        raise Exception('some values in secret config are missing')


class Main:
    def __init__(self):
        secret_config = read_json("secret.json")
        check_secret_config_integrity(secret_config)

        config = read_json("config.json")
        check_config_integrity(config)

        logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                            datefmt=database_date_time_format,
                            handlers=[
                                logging.FileHandler(
                                    "logs/" + datetime.datetime.now().strftime("%d-%m-%y_%H-%M") + ".log"),
                                logging.StreamHandler()
                            ],
                            level=logging.getLevelName(config["log-level"]))
        self.crawler = MyFitnessPalCrawler(secret_config["email"], secret_config["password"],
                                           config["friend-page-limit"], config['crawler-timeout'],
                                           config["crawler-max-retries"])
        self.db = SqliteConnector(config["database-path"])
        # initialise users
        self.db.create_users(config["initial-users"])
        self.mode = config['mode']

        self.sleep_time = config['sleep-time']
        self.timer = Timer()
        self.users_with_problems = []

    def re_login(self):
        self.crawler.login()

    def log_statistics(self):
        statistics = self.db.get_user_statistics()
        logging.info("Statistics: Found User: %i, Crawled Profiles: %i, Public Diaries: %i, Rate %.2f",
                     statistics['total'], statistics['profile-crawled'], statistics['public-diary'],
                     statistics['public-diary'] / statistics['profile-crawled'])

    def get_uncrawled_users(self):
        # no more users in queue get more from db
        uncrawled_users = []
        if self.mode == mode_friends:
            uncrawled_users = self.db.get_uncrawled_friends_users()
        if self.mode == mode_diaries:
            uncrawled_users = self.db.get_uncrawled_diaries_users()
        # filter all users with problems out
        uncrawled_users = [x for x in uncrawled_users if x not in self.users_with_problems]
        return uncrawled_users

    def crawl_profile(self, curr_user):
        # crawl profile information
        user_data = self.crawler.crawl_profile(curr_user.username)
        curr_user.gender = user_data['gender']
        curr_user.location = user_data['location']
        curr_user.has_public_diary = user_data['has_public_diary']
        curr_user.joined_date = user_data['joined']
        curr_user.age = user_data['age']
        curr_user.profile_crawl_time = datetime.datetime.now()
        self.db.save_user(curr_user)
        return curr_user

    def crawl_friends(self, curr_user):
        curr_user = self.crawl_profile(curr_user)
        # crawl friends
        friends = self.crawler.crawl_friends(curr_user.username)
        curr_user.friends_crawl_time = datetime.datetime.now()
        logging.info("crawled %i friends", len(friends))
        self.db.save_user(curr_user)
        self.db.create_users(friends)
        return curr_user

    def crawl_diary(self, curr_user):
        max_date = datetime.date(2021, 10, 1)
        from_date = curr_user.joined_date
        if not from_date:
            logging.info("%s has no joined date, last 5 years are crawled", curr_user.username)
            from_date = max_date - datetime.timedelta(days=365 * 5)
        to_date = from_date + datetime.timedelta(days=365)

        # check if there is already something for the user
        number_of_saved_meal_items = self.db.get_number_meal_items_from_user(curr_user)
        if number_of_saved_meal_items > 0:
            logging.warning("There is already a meal history for the user,... skipping")
            self.users_with_problems.append(curr_user)
            return curr_user
        while from_date < max_date:
            logging.info("crawl between %s, %s", from_date.strftime(database_date_format),
                         to_date.strftime(database_date_format))
            diary, ret = self.crawler.crawl_diary(curr_user.username, from_date, to_date)
            if ret == 'password':
                # password is required skip
                break
            if len(diary) == 1000:
                # only 1000 elements get crawled. After that it gets cut of at the front of the list
                # therefore if its 1000 elements crawl again from the from_date to the last crawled date
                # there is the possibility that the earliest date is not 100% complete therefore remove it and
                # crawl it again

                time.sleep(self.sleep_time)
                min_date = min(diary, key=lambda p: p['date'])['date']
                # first day was maybe not crawled 100%. Therefore remove it and crawl it again in the next step
                diary = [d for d in diary if d['date'] != min_date]
                logging.info("over 1000 diary entries, recrawl between %s and %s",
                             from_date.strftime(database_date_format),
                             min_date.strftime(database_date_format))
                diary_2, ret = self.crawler.crawl_diary(curr_user.username, from_date, min_date)
                logging.info("found additional %i entries", len(diary_2)-(1000-len(diary)))
                diary = diary_2 + diary
                if len(diary_2) == 1000:
                    # no implementation so far if the addition also expand over the limit.
                    raise Exception("Not implemented for such long diaries")

            # put in database
            logging.info("crawled %i diary entries of %s", len(diary), curr_user.username)

            self.timer.tick()
            for diary_entry in diary:
                item = self.db.get_meal_item(diary_entry['item'])
                if not item:
                    item = self.db.create_meal_item(diary_entry['item'])
                self.db.create_meal_history(curr_user.id, item.id, diary_entry['date'], diary_entry['meal'])
            delta = self.timer.tock("Database write")

            if self.sleep_time - delta > 0:
                time.sleep(self.sleep_time - delta)

            # update time
            from_date = to_date
            to_date = from_date + datetime.timedelta(days=365)
            if to_date > max_date:
                to_date = max_date

        curr_user.food_crawl_time = datetime.datetime.now()
        self.db.save_user(curr_user)
        return curr_user

    def main(self):
        relogin_time = time.time()
        logging.info("Starting with mode %s", self.mode)
        queue = deque()
        while True:
            if time.time() - relogin_time > 1800:
                # relogin every half hour
                self.re_login()
                relogin_time = time.time()
            if len(queue) == 0:
                # no more users in queue get more from db
                uncrawled_users = self.get_uncrawled_users()

                if len(uncrawled_users) == 0:
                    logging.info("No more uncrawled users. Abort...")
                    break
                logging.info("Requested %i uncrawled users from DB", len(uncrawled_users))
                queue.extend(uncrawled_users)
            curr_user = queue.popleft()
            logging.info("Crawling %s", curr_user.username)
            if self.mode == mode_friends:
                self.log_statistics()
                curr_user = self.crawl_friends(curr_user)

            if self.mode == mode_diaries:
                curr_user = self.crawl_diary(curr_user)


if __name__ == '__main__':
    main = Main()
    main.main()
