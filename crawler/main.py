#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:35:39 2021

@author: gregor
"""
import logging

from helper.event import EventController, Event
from helper.timer import Timer
from helper.configIntegrityChecker import ConfigIntegrityChecker
from mfpCrawler.crawler import MyFitnessPalCrawler
import json
from collections import deque
import datetime
import time
import shutil
from databaseConnector.databaseConnector import SqliteConnector, database_date_format, database_date_time_format, User

# read the secrets from file

mode_friends = 'friends'
mode_diaries = 'diaries'
mode_profile = 'profile'
mode_diaries_test = 'diaries-test'

# datetime format used in filenames
file_datetime_format = "%d-%m-%y_%H-%M"


def check_config_integrity(config):
    """
    Checks if the config is as expected
    :param config: config object
    :type config: dict
    """
    c = ConfigIntegrityChecker(config)

    c.check_float('sleep-time-diary')
    c.check_float('sleep-time-profile')
    c.check_set('mode', (mode_friends, mode_diaries, mode_diaries_test, mode_profile))
    c.check_str('database-path')
    c.check_str('database-backup-folder')
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


def relogin_callback(crawler: MyFitnessPalCrawler):
    logging.info("Relogin to circumvent logout")
    crawler.login()


def save_db_callback(src_path, backup_folder):
    backup_folder = backup_folder.rstrip('/')
    backup_file_path = f"{backup_folder}/{datetime.datetime.now().strftime(file_datetime_format)}.db"
    logging.info("Creating copy of DB...")
    shutil.copy(src_path, backup_file_path)
    logging.info("DB saved at %s", backup_file_path)


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
                                    "logs/" + datetime.datetime.now().strftime(file_datetime_format) + ".log"),
                                logging.StreamHandler()
                            ],
                            level=logging.getLevelName(config["log-level"]))
        self.crawler = MyFitnessPalCrawler(secret_config["email"], secret_config["password"],
                                           config["friend-page-limit"], config['crawler-timeout'],
                                           config["crawler-max-retries"])
        self.db = SqliteConnector(config["database-path"])

        self.mode = config['mode']
        self.test_users = []
        self.sleep_time_diary = config['sleep-time-diary']
        self.sleep_time_profile = config['sleep-time-profile']
        self.timer = Timer()
        self.users_with_problems = []
        # initialise users if not exists
        self.db.create_users(config["initial-users"])
        if self.mode == mode_diaries_test:
            self.test_users = [self.db.get_user_by_username(x) for x in config["initial-users"]]

        self.meal_items = []
        self.diary_timeout_count = 0

        # init the events
        self.event_queue = EventController()
        re_login_event = Event(relogin_callback, hour=1, args=[self.crawler], instant=False)
        save_db_event = Event(save_db_callback, hour=8, args=[config["database-path"],
                                                              config["database-backup-folder"]])
        self.event_queue.add_event(re_login_event)
        self.event_queue.add_event(save_db_event)

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
        if self.mode == mode_profile:
            uncrawled_users = self.db.get_uncrawled_profile_users()
        if self.mode == mode_diaries_test:
            uncrawled_users = self.test_users
            self.test_users = []
        # filter all users with problems out
        uncrawled_users = [x for x in uncrawled_users if x not in self.users_with_problems]
        return uncrawled_users

    def crawl_profile(self, curr_user: User):
        # crawl profile information
        self.timer.tick()
        user_data = self.crawler.crawl_profile(curr_user.username)
        curr_user.gender = user_data['gender']
        curr_user.location = user_data['location']
        curr_user.has_public_diary = user_data['has_public_diary']
        curr_user.joined_date = user_data['joined']
        curr_user.age = user_data['age']
        curr_user.profile_crawl_time = datetime.datetime.now()
        self.db.save_user(curr_user)
        delta = self.timer.tock_s()

        if self.sleep_time_profile - delta > 0:
            time.sleep(self.sleep_time_profile - delta)

        return curr_user

    def crawl_friends(self, curr_user: User):
        curr_user = self.crawl_profile(curr_user)
        # crawl friends
        friends = self.crawler.crawl_friends(curr_user.username)
        curr_user.friends_crawl_time = datetime.datetime.now()
        logging.info("crawled %i friends", len(friends))
        self.db.save_user(curr_user)
        self.db.create_users(friends)
        return curr_user

    def crawl_diary(self, curr_user: User):
        """
        max_date = datetime.date(2021, 10, 1)
        from_date = curr_user.joined_date
        if not from_date:
            logging.info("%s has no joined date, last 5 years are crawled", curr_user.username)
            from_date = max_date - datetime.timedelta(days=365 * 5)
        to_date = from_date + datetime.timedelta(days=365)
        """
        self.timer.tick()
        no_of_entries = 0
        to_date = datetime.date(2021, 10, 1)
        from_date = to_date - datetime.timedelta(days=365)
        cutoff_date = curr_user.joined_date
        if cutoff_date is None:
            logging.info("%s has no joined date, last 5 years are crawled", curr_user.username)
            cutoff_date = to_date - datetime.timedelta(days=365 * 5)

        # check if there is already something for the user
        number_of_saved_meal_items = self.db.get_number_meal_items_from_user(curr_user)
        if number_of_saved_meal_items > 0:
            logging.warning("There is already a meal history for the user,... skipping")
            self.users_with_problems.append(curr_user)
            return curr_user
        while to_date > cutoff_date:
            logging.info("crawl between %s, %s", from_date.strftime(database_date_format),
                         to_date.strftime(database_date_format))
            diary, ret = self.crawler.crawl_diary(curr_user.username, from_date, to_date)
            if ret == 'skip':
                # somethings wrong skip this user
                break
            if ret == 'timeout':
                logging.warning("Timeout for user %s, skip profiles")
                self.diary_timeout_count += 1
                if self.diary_timeout_count > 2:
                    logging.exception("Too many timeouts in a row, something is not right")
                    raise Exception("Too many timeouts in a row, something is not right")
                break
            # update time
            if len(diary) == 1000:
                # only 1000 elements get crawled. After that it gets cut of at the front of the list
                # therefore if its 1000 elements crawl again from the from_date to the last crawled date
                # there is the possibility that the earliest date is not 100% complete therefore remove it and
                # crawl it again in the next step
                min_diary_date = min(diary, key=lambda p: p['date'])['date']
                logging.info("found over 1000 diary entries for this period, recrawl between %s and %s",
                             from_date.strftime(database_date_format),
                             min_diary_date.strftime(database_date_format))
                # first day was maybe not crawled 100%. Therefore remove it and crawl it again in the next step
                diary = [d for d in diary if d['date'] != min_diary_date]
                to_date = min_diary_date
            else:
                to_date = from_date - datetime.timedelta(days=1)
                from_date = to_date - datetime.timedelta(days=365)
                if from_date < cutoff_date:
                    from_date = cutoff_date
            no_of_entries += len(diary)
            if no_of_entries > 0:
                self.diary_timeout_count = 0
            # put in database
            logging.info("insert %i diary entries of %s in database", len(diary), curr_user.username)
            self.timer.tick()
            for diary_entry in diary:
                item = self.db.get_meal_item(diary_entry['item'])
                if not item:
                    item = self.db.create_meal_item(diary_entry['item'])
                self.db.create_meal_history(curr_user.id, item.id, diary_entry['date'], diary_entry['meal'])
            delta = self.timer.tock("Database write")

            if self.sleep_time_diary - delta > 0:
                time.sleep(self.sleep_time_diary - delta)

        curr_user.food_crawl_time = datetime.datetime.now()
        self.db.save_user(curr_user)
        meal_statistics = self.db.get_meal_statistics()
        crawl_time = self.timer.tock_s()
        logging.info(f"Crawling of %s took %.2f with %i items", curr_user.username, crawl_time, no_of_entries)
        logging.info(f"On average takes crawling %.2f with %i items", meal_statistics['avg-time'], meal_statistics['avg-entries'])
        self.db.create_meal_statistic(curr_user, crawl_time, no_of_entries)
        return curr_user

    def main(self):
        # relogin_time = time.time()
        logging.info("Starting with mode %s", self.mode)
        queue = deque()
        while True:
            self.event_queue.check_events()
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
            if self.mode == mode_profile:
                curr_user = self.crawl_profile(curr_user)
            if self.mode == mode_diaries_test:
                # delete old diary entry
                self.db.delete_meal_history_for_user(curr_user)
                curr_user.food_crawl_time = None
                self.db.save_user(curr_user)
                # crawl new diary
                curr_user = self.crawl_diary(curr_user)


if __name__ == '__main__':
    main = Main()
    try:
        main.main()
    except Exception as e:
        logging.exception(e)
        raise e
