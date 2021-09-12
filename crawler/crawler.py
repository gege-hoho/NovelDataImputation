#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 08:49:48 2021

@author: gregor
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
import re
logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S', 
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.NOTSET)
user_endpoint = "https://www.myfitnesspal.com/profile/{0}"
login_endpoint= "https://www.myfitnesspal.com/account/login"
friends_endpoint = "https://www.myfitnesspal.com/user/{0}friends/list"
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "accept-language": "en-EN,en;q=0.9"
}
#checks if the username is currently logged in
def logged_in(page_text):
    soup = BeautifulSoup(page_text, 'html.parser')
    links = [x.get("href")for x in soup.find_all("a")]
    logged = '/account/logout' in links
    if not logged:
        logging.warn("it seems that  we aren't logged in anymore")
    return logged
    

def login(email,password):
    session = requests.Session()
    r = session.get(login_endpoint, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    auth_token = soup.find(class_="form login LoginForm").find(attrs={"name": "authenticity_token"})["value"]
    payload = {"utf8": "✓",
               "authenticity_token": auth_token,
               "username": email,
               "password": password,
               "remember_me": 1}
    r = session.post(login_endpoint, data=payload, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    if soup.find(class_="sub-nav") and logged_in(r.text):
        logging.info("%s logged in",email)
        return session
    logging.error("login failed for %s", email)
    logging.error(r.text)


#read the secrets from file
f = open("secret.json",'r')
secret_config = json.loads(f.read())
session = login(secret_config["email"],secret_config["password"])

username = "Theo166"
logging.info("Request profile of %s", username)
r = session.get(user_endpoint.format(username))
logged_in(r.text)
soup = BeautifulSoup(r.text, 'html.parser')
links = [x.get("href")for x in soup.find_all("a")]
has_public_diary = (f"/food/diary/{username}" in links)

profile_soup = soup.find("div", id="profile")
gender=""
if "Female" in profile_soup.text:
    gender="f"
elif "Male" in profile_soup.text:
    gender="m"
else:
    logging.warning("Could not detect gender for %s", username)


joined_re = re.compile("Member\s*since\s*([a-zA-Z]*\s*[0-9],\s*[0-9]{4})") 
joined=re.findall(joined_re, profile_soup.text)
if len(joined) == 0:
    logging.warning("Could not detect joined date")
    joined = [""]
elif len(joined) >1:
    logging.warning("Found more than expected joined date: %s", " ".join(joined))
joined = joined[0]



