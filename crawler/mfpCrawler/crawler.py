#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 08:49:48 2021

@author: gregor
"""

import requests
import datetime
from bs4 import BeautifulSoup, element
import logging
import re
import mfpCrawler.endpoints as endpoints

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "accept-language": "en-EN,en;q=0.9"
}


def detect_meal(meal):
    """
    Formats the string and converts it to one of the meal types
    :param meal: str
    :type meal:
    :return: meal type (b,l,d,s,u)
    :rtype: str
    """
    meal_string = meal.strip().replace("\n", "").lower()
    if meal_string == 'breakfast':
        return 'b'
    if meal_string == 'lunch':
        return 'l'
    if meal_string == 'dinner':
        return 'd'
    if meal_string == 'snacks':
        return 's'
    logging.warning('could not detect %s', meal)
    return 'u'  # unkown


def process_nutrient(nutrient, expected_unit=None):
    """

    :param nutrient: The nutrient to be process eg. 5g
    :type nutrient: str
    :param expected_unit: The expected unit eg. mg or g or none if no unit
    :type expected_unit: str
    :return: int
    :rtype: int
    """
    n = nutrient.replace(',','')
    if expected_unit:
        n = n.split(expected_unit)[0]

    if n.isnumeric():
        return int(n)
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


# extract food information for one day of food entry
def extract_food(soup, date):
    # nutrients = [x.text for x in soup.find('thead').find_all('td')]
    food_item_soups = soup.find('tbody').find_all("tr")
    meal = ""
    food_items = []
    for food_item_soup in food_item_soups:
        curr_class = food_item_soup.get('class')
        curr_name = food_item_soup.name
        if curr_class is not None and 'title' in curr_class:
            meal = detect_meal(food_item_soup.text)
            # logging.debug(meal)
            continue
        if curr_name == 'tr':
            infos = [x.text for x in food_item_soup.find_all('td')]
            food_item = create_food_entry(date, meal, infos[0], infos[1], infos[2],
                                          infos[3], infos[4], infos[5],
                                          infos[6], infos[7], infos[8])
            food_items.append(food_item)
    return food_items


def extract_exercise(soup):
    pass


class MyFitnessPalCrawler:
    def __init__(self, email, password):
        self.session = requests.Session()
        self.friend_page_limit = 100
        # conatins the last request
        self.last_request = None
        self.login(email, password)

    def get(self, endpoint):
        r = self.session.get(endpoint, headers=headers)
        self.last_request = BeautifulSoup(r.text, 'html.parser')
        return self.last_request

    def post(self, endpoint, payload):
        r = self.session.post(endpoint, data=payload, headers=headers)
        self.last_request = BeautifulSoup(r.text, 'html.parser')
        return self.last_request

    # sets the self.session and tries to login
    def login(self, email, password):
        soup = self.get(endpoints.login_endpoint)
        auth_token = soup.find(class_="form login LoginForm").find(attrs={"name": "authenticity_token"})["value"]
        payload = {"utf8": "✓",
                   "authenticity_token": auth_token,
                   "username": email,
                   "password": password,
                   "remember_me": 1}
        soup = self.post(endpoints.login_endpoint, payload)
        if soup.find(class_="sub-nav") and self.logged_in():
            logging.info("%s logged in", email)
        else:
            logging.error("login failed for %s", email)
            logging.error(self.last_request.text)

    # checks if the username is currently logged in
    def logged_in(self):
        soup = self.last_request
        links = [x.get("href") for x in soup.find_all("a")]
        logged = '/account/logout' in links
        if not logged:
            logging.warn("it seems that  we aren't logged in anymore")
        return logged

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
            "location": None
        }
        logging.info("Request profile of %s", username)
        soup = self.get(endpoints.user_endpoint.format(username))
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

        if 2 <= len(profile_text) <= 3:
            if "Female" in profile_text:
                user_data["gender"] = "f"
            elif "Male" in profile_text:
                user_data["gender"] = "m"
            else:
                logging.warning("Could not detect gender for %s", username)
            joined_re = re.compile("Member\s*since\s*([a-zA-Z]*\s*[0-9]{1,2},\s*[0-9]{4})")
            joined = re.findall(joined_re, profile_text[-1])
            if len(joined) == 0:
                logging.warning("Could not detect joined date")
                joined = [""]
            elif len(joined) > 1:
                logging.warning("Found more than expected joined date: %s", " ".join(joined))
            user_data["joined"] = datetime.datetime.strptime(joined[0], '%B %d, %Y').date()

            # this means that a location is public
            if len(profile_text) == 3:
                user_data["location"] = profile_text[1]
        elif len(profile_text) == 0 and soup.find("div", {"id": "profile-private"}):
            logging.info("Profile is private")
        else:
            logging.warning("Profile info length mismatch. It should be between 2 and 3, but was %i", len(profile_text))

        logging.debug("Sucessfulley crawled %s", str(user_data))
        return user_data

    def crawl_friends(self, username):
        logging.info("Request friend list of %s", username)
        i = 0
        friends = []
        while True:
            i += 1
            soup = self.get(endpoints.friends_endpoint.format(username, i))
            no_friend = soup.find("div", {"class": "no_friends"})
            if no_friend:
                if "friends list is viewable by friends only" in no_friend.text.strip():
                    logging.info("%s does not have their friend public", username)
                    pass
                elif "currently does not have any friends added" in no_friend.text.strip() and i == 1:
                    logging.info("%s does not have friends", username)
                    pass
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

        soup = self.get(endpoints.diary_endpoint.format(username,
                                                        from_date.strftime(date_format),
                                                        to_date.strftime(date_format)))

        dates = soup.find("h2", {"id": "date"}).previous_sibling
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
            elif sibling.get('id') == 'excercise':
                # exercise entry
                extract_exercise(sibling)
            elif sibling.get('id') == 'food':
                # food_entry
                x = extract_food(sibling, current_date)
                data.extend(x)
                logging.debug(str(x))
            else:
                logging.warning('Unexpected tag %s', str(sibling))

        return data
