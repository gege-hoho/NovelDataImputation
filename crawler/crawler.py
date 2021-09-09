#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 08:49:48 2021

@author: gregor
"""

import requests
from bs4 import BeautifulSoup
import json

user_endpoint = "https://www.myfitnesspal.com/profile/{0}"
login_endpoint= "https://www.myfitnesspal.com/account/login"
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "accept-language": "en-EN,en;q=0.9"
}

def login(username,password):
    session = requests.Session()
    r = session.get(login_endpoint, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    auth_token = soup.find(class_="form login LoginForm").find(attrs={"name": "authenticity_token"})["value"]
    payload = {"utf8": "✓",
               "authenticity_token": auth_token,
               "username": username,
               "password": password,
               "remember_me": 1}
    r = session.post(login_endpoint, data=payload, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    if soup.find(class_="sub-nav"):
        print("logged in")
        return session
    print("login failed")
    
#read the secrets from file
f = open("secret.json",'r')
secret_config = json.loads(f.read())
session = login(secret_config["username"],secret_config["password"])
