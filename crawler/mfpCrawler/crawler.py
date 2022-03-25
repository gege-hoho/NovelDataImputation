#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 08:49:48 2021

@author: gregor
"""
import time

import requests
from requests.exceptions import Timeout
from translate import Translator
from langdetect import detect
import datetime
from bs4 import BeautifulSoup, element
import logging
import re
import mfpCrawler.endpoints as endpoints
from helper.helper import convert_int

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "accept-language": "en-EN,en;q=0.9"
}


def process_nutrient(nutrient, expected_unit=None):
    """

    :param nutrient: The nutrient to be process eg. 5g
    :type nutrient: str
    :param expected_unit: The expected unit eg. mg or g or none if no unit
    :type expected_unit: str
    :return: int
    :rtype: int
    """
    n = nutrient.replace(',', '')
    if expected_unit:
        n = n.split(expected_unit)[0]

    x = convert_int(n)
    if x is not None:
        return x
    elif n == '--':
        return None
    else:
        logging.error("Cant process nutrient %s with %s", nutrient, expected_unit)
        return None


def create_food_entry(date, meal, name, calories, carbs, fat, protein, cholest, sodium, sugars, fiber):
    """
    Creates food item entry
    :return: Food item entry
    :rtype: dict
    """
    return {'date': date,
            'meal': meal,
            'item': {
                'name': name,
                'calories': process_nutrient(calories),
                'carbs': process_nutrient(carbs, 'g'),
                'fat': process_nutrient(fat, 'g'),
                'protein': process_nutrient(protein, 'g'),
                'cholest': process_nutrient(cholest, 'mg'),
                'sodium': process_nutrient(sodium, 'mg'),
                'sugars': process_nutrient(sugars, 'g'),
                'fiber': process_nutrient(fiber, 'g')
            }
            }


def pre_processor(text: str):
    """
    Does General Preprocessing on the get
    :param text:
    :type text:
    :return:
    :rtype:
    """
    text = text.replace(u'\xa0', ' ')
    return text


def error_callback(t):
    """
    Callback function for get and post that is called as default
    :param t:
    :type t: Timeout
    """
    raise t


class MyFitnessPalCrawler:
    def __init__(self, email, password, friend_page_limit=100, timeout=5, max_retries=5, use_translation=False):
        self.use_translation = use_translation
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.translations = []
        self.friend_page_limit = friend_page_limit
        # conatins the last request
        self.last_request = None
        self.data = (email, password)
        self.login()

    def get(self, endpoint, callback=error_callback):
        """
        Sends a get request to the given endpoint retries max_retries times with a timeout
        If the request fails max_retries times, the error callback is called with the Timeout
        as Argument
        :param endpoint: endpoint
        :type endpoint: str
        :param callback: callback function
        :type callback: func
        :return: request, statuscode
        :rtype:
        """
        i = 0
        while i < self.max_retries:
            try:
                r = self.session.get(endpoint, headers=headers, timeout=self.timeout)
                if r.status_code != 200:
                    logging.warning("Not 200 status code !")
                text = pre_processor(r.text)
                self.last_request = BeautifulSoup(text, 'html.parser')
                return self.last_request, r.status_code
            except Timeout as t:
                i += 1
                logging.warning("Timeout during request at %s retry %i out of %i", endpoint, i, self.max_retries)
                if i == self.max_retries:
                    return callback(t)
            except ConnectionError as e:
                i += 1
                logging.warning("Connection error %s", e)
                time.sleep(1)
                self.session = requests.Session()
                self.login()
                if i == self.max_retries:
                    return callback(e)

    def post(self, endpoint, payload, callback=error_callback):
        """
        Sends a post request to the given endpoint with payload, retries max_retries times with a timeout
        If the request fails max_retries times, the error callback is called with the Timeout
        as Argument
        :param payload: payload
        :type payload: dict
        :param endpoint: endpoint
        :type endpoint: str
        :param callback: callback function
        :type callback: func
        :return: request, statuscode
        :rtype:
        """
        i = 0
        r = None
        while i < self.max_retries:
            try:
                r = self.session.post(endpoint, data=payload, headers=headers, timeout=self.timeout)
                if r.status_code != 200:
                    logging.warning("Not 200 status code !")
                text = pre_processor(r.text)
                self.last_request = BeautifulSoup(text, 'html.parser')
                return self.last_request, r.status_code
            except Timeout as t:
                i += 1
                logging.warning("Timeout during request at %s retry %i out of %i", endpoint, i, self.max_retries)
                if i == self.max_retries:
                    return callback(t)
            except ConnectionError as e:
                i += 1
                logging.warning("Connection error %s", e)
                time.sleep(1)
                self.session = requests.Session()
                self.login()
                if i == self.max_retries:
                    return callback(e)

    def login(self):
        """
        Sets the self.session and tries to login using the data given at Object creation
        """
        email, password = self.data
        logging.info("Login into %s", email)
        soup, _ = self.get(endpoints.login_endpoint)
        auth_token = soup.find(class_="form login LoginForm").find(attrs={"name": "authenticity_token"})["value"]
        payload = {"utf8": "✓",
                   "authenticity_token": auth_token,
                   "username": email,
                   "password": password,
                   "remember_me": 1}
        soup, _ = self.post(endpoints.login_endpoint, payload)
        if soup.find(class_="sub-nav"):
            logging.info("%s logged in", email)
        else:
            logging.error("login failed for %s", email)
            logging.error(self.last_request.text)

    def logged_in(self):
        """
        Checks if the username is currently logged in, based on the last request
        :return: is logged_in
        :rtype: bool
        """
        soup = self.last_request
        links = [x.get("href") for x in soup.find_all("a")]
        logged = '/account/logout' in links
        if not logged:
            logging.warning("it seems that  we aren't logged in anymore")
            logging.info("Relogin")
            self.login()
        return logged

    def extract_food(self, soup, date):
        """
        extract food information for one day of food entry
        :param soup: Soup from which the data should be extracted
        :type soup:
        :param date: current date
        :type date: date
        :return: List of food items
        :rtype: list
        """
        # nutrients = [x.text for x in soup.find('thead').find_all('td')]
        food_item_soups = soup.find('tbody').find_all("tr")
        meal = ""
        food_items = []
        for food_item_soup in food_item_soups:
            curr_class = food_item_soup.get('class')
            curr_name = food_item_soup.name
            if curr_class is not None and 'title' in curr_class:
                meal = self.detect_meal(food_item_soup.text)
                # logging.debug(meal)
                continue
            if curr_name == 'tr':
                infos = [x.text for x in food_item_soup.find_all('td')]
                food_item = create_food_entry(date, meal, infos[0], infos[1], infos[2],
                                              infos[3], infos[4], infos[5],
                                              infos[6], infos[7], infos[8])
                food_items.append(food_item)
        return food_items

    def translate_meal_string(self, meal_string):
        # check if we already entcountered this meal_string
        translation = next((b for (a, b) in self.translations if a == meal_string), None)
        if translation:
            return translation
        try:
            translator = Translator(to_lang='en', from_lang=detect(meal_string))
            translation = translator.translate(meal_string)
        except:
            translation = meal_string

        translation = translation.strip().replace("\n", "").lower()
        logging.info("Translated %s to %s", meal_string, translation)
        if translation == 'snack':
            translation = 'snacks'
        return translation

    def detect_meal(self, meal):
        """
        Formats the string and converts it to one of the meal types
        :param meal: str
        :type meal:
        :return: meal type
        :rtype: str
        """
        meal_types = ['breakfast', 'lunch', 'dinner', 'snacks', 'dessert']
        meal_string = meal.strip().replace("\n", "").lower()

        match = re.compile("meal ([0-9])").match(meal_string)
        if match:
            return match.group(0)  # 0 or 1,2,...
        if meal_string in meal_types:
            return meal_string

        if self.use_translation:
            translation = self.translate_meal_string(meal_string)
            if translation in meal_types:
                logging.debug("added %s %s to translation", meal_string, translation)
                self.translations.append((meal_string, translation))
                return translation
            # we couldn't match the translated meal_string. Therefore we throw away the translation and save it as is
            self.translations.append((meal_string, meal_string))
            logging.info("couldn't match %s", meal_string)
        return meal_string

    def crawl_profile(self, username):
        """
        Crawls the profile of an user

        :param username: username
        :type username: str
        :return: Dict containing profile data
        :rtype: dict
        """
        user_data = {
            "username": username,
            "has_public_diary": None,
            "gender": None,
            "joined": None,
            "location": None,
            "age": None
        }
        logging.info("Request profile of %s", username)
        soup, code = self.get(endpoints.user_endpoint.format(username))
        if code == 404:
            # user page not found bye bye
            return user_data
        self.logged_in()
        links = [x.get("href") for x in soup.find_all("a")]
        user_data["has_public_diary"] = (f"/food/diary/{username}" in links)

        profile_soup = soup.find("div", id="profile")
        if profile_soup is None:
            if "has deactivated their account" in soup.text:
                logging.info("Account is deactivated")
            else:
                logging.warning("Could not detect profile unknown problem")
            return user_data

        profile_soup = profile_soup.find("div", {'class': "col-2"}).find_all("h5")
        profile_text = [x.text for x in profile_soup]
        # profile_text = [x for x in profile_text if 'years old' not in x] # skip age if there

        if 2 <= len(profile_text) <= 4:
            for index, text in enumerate(profile_text):
                age_re = re.compile("(\d\d) years old")
                age = re.findall(age_re, text)

                joined_re = re.compile("Member\s*since\s*([a-zA-Z]*\s*[0-9]{1,2},\s*[0-9]{4})")
                joined = re.findall(joined_re, text)

                location_re = re.compile("(.*, [A-Z][A-Z])")
                location = re.findall(location_re, text)

                if age:
                    if len(age) != 1:
                        logging.warning("Could not detect single age")
                        continue
                    user_data["age"] = age[0]
                elif text in ("Male", "Female"):
                    if "Female" in text:
                        user_data["gender"] = "f"
                    elif "Male" in text:
                        user_data["gender"] = "m"
                elif joined:
                    if len(joined) != 1:
                        logging.warning("Could not detect single joined date")
                        continue
                    user_data["joined"] = datetime.datetime.strptime(joined[0], '%B %d, %Y').date()
                elif location:
                    if len(location) != 1:
                        logging.warning("Could not detect single location")
                    user_data["location"] = text

        elif len(profile_text) == 0 and soup.find("div", {"id": "profile-private"}):
            logging.info("Profile is private")
        else:
            logging.warning("Profile info length mismatch. It should be between 2 and 3, but was %i", len(profile_text))

        logging.debug("Sucessfulley crawled %s", username)
        return user_data

    def crawl_friends(self, username):
        logging.info("Request friend list of %s", username)
        i = 0
        friends = []
        while True:
            i += 1
            soup, _ = self.get(endpoints.friends_endpoint.format(username, i))
            no_friend = soup.find("div", {"class": "no_friends"})
            title = soup.find("h1", {"class": "main-title"})
            if title and title.text == "Unknown User":
                logging.info("User %s not known abort", username)
                break
            if no_friend:
                if "friends list is viewable by friends only" in no_friend.text.strip():
                    logging.info("%s does not have their friend public", username)
                elif "currently does not have any friends added" in no_friend.text.strip() and i == 1:
                    logging.info("%s does not have friends", username)
                # no more friends we're done
                break
            if i == self.friend_page_limit:
                logging.warning("Hit the limit of Friend Pages for %s", username)
                break

            curr_friends = [x.get("href").split('/profile/')[1] for x in soup.find_all("a", {"class": "user"})]
            if len(curr_friends) == 0:
                logging.error("Did not found friends, but expected at least 1 for %s", username)
            friends.extend(curr_friends)
        return friends

    def crawl_diary(self, username, from_date, to_date):
        date_format = '%Y-%m-%d'
        if datetime.timedelta(days=0) < to_date - from_date > datetime.timedelta(days=365):
            logging.error("Cannot crawl diary from %s to %s",
                          from_date.strftime(date_format),
                          to_date.strftime(date_format))

        soup, status = self.get(endpoints.diary_endpoint.format(username,
                                                                from_date.strftime(date_format),
                                                                to_date.strftime(date_format)),
                                callback=lambda _: (None, 999))
        if status == 999:
            return [], 'timeout'
        title = soup.find('h1', {'class': 'main-title'})
        if title is not None:
            if title.text == 'Password Required':
                logging.info("Password required to enter diary")
                return [], 'skip'
            if title.text == 'This Username is Invalid':
                logging.warning("Username is no longer valid")
                return [], 'skip'
            if title.text == 'This Diary is Private':
                logging.warning("This Diary is Private")
                return [], 'skip'

        dates = soup.find("h2", {"id": "date"})
        if dates and dates.text == 'No diary entries were found for this date range.':
            logging.info("No diary entries were found for the date range")
            return [], 'range'
        if dates is None:
            logging.error("Unkown Error, could not detect dates on the site")
            logging.error(soup.prettify())
            return [], 'skip'
        dates = dates.previous_sibling
        data = []
        current_date = None
        for sibling in dates.next_siblings:
            if type(sibling) is not element.Tag:
                # current node is no html tag therefore skip it
                continue
            if sibling.get('id') == 'date':
                # new date
                current_date = datetime.datetime.strptime(sibling.text, '%B %d, %Y').date()
                # logging.debug(current_date)
            elif sibling.get('id') == 'excercise':  # spelling mistake on purpose it's in the html as well
                # exercise entry ignore for now
                pass
            elif sibling.get('id') == 'food':
                # food_entry
                x = self.extract_food(sibling, current_date)
                data.extend(x)
            elif sibling.get('class') == ['notes']:
                # we ignore notes for now
                pass
            else:
                logging.warning('Unexpected tag %s', str(sibling))

        return data, None
