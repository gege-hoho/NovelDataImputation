#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 08:49:48 2021

@author: gregor
"""

import requests
from collections import deque
from bs4 import BeautifulSoup
import json
import logging
import re
import endpoints

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S', 
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.NOTSET)

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "accept-language": "en-EN,en;q=0.9"
}

class MyFitnessPalCrawler:
    def __init__(self,email,password):
        self.session = requests.Session()
        self.friend_page_limit = 100
        #conatins the last request
        self.last_request = None
        self.login(email,password)
        
    def get(self,endpoint):
        r = self.session.get(endpoint, headers=headers)
        self.last_request = BeautifulSoup(r.text, 'html.parser')
        return self.last_request
    
    def post(self,endpoint, payload):
        r = self.session.post(endpoint, data=payload, headers=headers)
        self.last_request = BeautifulSoup(r.text, 'html.parser')
        return self.last_request
    
    
    #sets the self.session and tries to login
    def login(self,email,password):
        soup = self.get(endpoints.login_endpoint)
        auth_token = soup.find(class_="form login LoginForm").find(attrs={"name": "authenticity_token"})["value"]
        payload = {"utf8": "✓",
                   "authenticity_token": auth_token,
                   "username": email,
                   "password": password,
                   "remember_me": 1}
        soup = self.post(endpoints.login_endpoint, payload)
        if soup.find(class_="sub-nav") and self.logged_in():
            logging.info("%s logged in",email)
        else:
            logging.error("login failed for %s", email)
            logging.error(self.last_request.text)

    #checks if the username is currently logged in
    def logged_in(self):
        soup = self.last_request
        links = [x.get("href")for x in soup.find_all("a")]
        logged = '/account/logout' in links
        if not logged:
            logging.warn("it seems that  we aren't logged in anymore")
        return logged
    

    def crawl_profile(self,username):
        user_data={
            "username": username,
            "has_public_diary": None,
            "gender": None,
            "joined": None,
            "location": None
            }
        logging.info("Request profile of %s", username)
        soup = self.get(endpoints.user_endpoint.format(username))
        self.logged_in()
        links = [x.get("href")for x in soup.find_all("a")]
        user_data["has_public_diary"] = (f"/food/diary/{username}" in links)
        
        profile_soup = soup.find("div", id="profile").find("div", {'class':"col-2"}).find_all("h5")
        profile_text = [x.text for x in profile_soup]
        
        if 2 <= len(profile_text) <= 3:
            if "Female" in profile_text:
                user_data["gender"]="f"
            elif "Male" in profile_text:
                user_data["gender"]="m"
            else:
                logging.warning("Could not detect gender for %s", username)
            joined_re = re.compile("Member\s*since\s*([a-zA-Z]*\s*[0-9]{1,2},\s*[0-9]{4})") 
            joined=re.findall(joined_re, profile_text[-1])
            if len(joined) == 0:
                logging.warning("Could not detect joined date")
                joined = [""]
            elif len(joined) >1:
                logging.warning("Found more than expected joined date: %s", " ".join(joined))
            user_data["joined"] = joined[0]
            
            #this means that a location is public
            if len(profile_text) == 3:
                user_data["location"]= profile_text[1]
        else:
            logging.warning("Profile info length mismatch. It should be between 2 and 3")
            
        logging.debug("Sucessfulley crawled %s", str(user_data))
        return(user_data)
    
    def crawl_friends(self,username):
        logging.info("Request friend list of %s", username)
        i = 0
        friends = []
        while(True):
            i+=1
            soup = self.get(endpoints.friends_endpoint.format(username,i))
            no_friend = soup.find("div",{"class":"no_friends"})
            if no_friend:
                if "friends list is viewable by friends only" in no_friend.text.strip():
                    logging.info("%s does not have their friend public", username)
                    pass
                elif "currently does not have any friends added" in no_friend.text.strip() and i == 1:
                    logging.info("%s does not have friends",username)
                    pass
                #no more friends we're done
                break
            if i == self.friend_page_limit:
                logging.warning("Hit the limit of Friend Pages for %s", username)
                break
            
            curr_friends = [x.get("href").split('/profile/')[1]for x in soup.find_all("a",{"class":"user"})]
            if len(curr_friends) == 0:
                logging.error("Did not found friends, but expected at least 1 for %s", username)
            friends.extend(curr_friends)
        return friends
    
#read the secrets from file
f = open("secret.json",'r')
secret_config = json.loads(f.read())
self =MyFitnessPalCrawler(secret_config["email"],secret_config["password"])
#x.crawl_profile("Theo166")
#x.crawl_profile("PrincessLou71186")
username = "amgjb"
self.crawl_profile(username)

queue = deque()
queue.append("Theo166")

crawled = []
for i in range(30):
    curr_user = queue.popleft()
    friends = self.crawl_friends(curr_user)
    crawled.append(curr_user)
    queue.extend([x for x in friends if x not in queue and x not in crawled])


