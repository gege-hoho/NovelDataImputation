#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  5 15:23:30 2022

@author: gregor
"""

import pickle
import datetime
import sqlite3
import pandas as pd
import numpy as np

con = sqlite3.connect("preProcessor/data/mfp.db")

def get_interaction(con,year):
    cur = con.cursor()
    cur.execute(f"""select count(*), date 
                from meal_history_flat where date like '%-{str(year)}'group by date""")
    res = cur.fetchall()
    #res = [x[0] for x in res]
    res = [(x,datetime.datetime.strptime(y,'%d-%m-%y').date()) for x,y in res]
    cur.close()
    return res

def get_user_info(con,user):
    cur = con.cursor()
    cur.execute(f"""select * from user where user = {user}""")
    res = cur.fetchall()
    cur.close()
    res = res[0]
    return {"user": res[0], "gender": res[2], "age": res[9],"location": res[3]}

def get_categories(flat_list):
    categories = {"breakfast":{},
              "lunch":{},
              "dinner": {},
              "snacks": {}}
    for x in flat_list:
        meal_dict = categories[x['meal']]
        for y in x['category']:
            if y not in meal_dict:
                meal_dict[y] = 0
            meal_dict[y] += 1
    new_categories = {}    
    for k,v in categories.items():
        l = [(k, v) for k, v in v.items()]
        l.sort(key=lambda x: x[1],reverse=True)
        new_categories[k] = l
    return new_categories

with open("preProcessor/time_data_enorm.pickle", 'rb') as file:
    data = pickle.load(file)

spring = range(80, 172)
summer = range(172, 264)
fall = range(264, 355)
winter = list(range(80))
winter.extend(range(355,366))

flat_list = [item for sublist in data for item in sublist]
list_spring = [x for x in flat_list if x["date"].timetuple().tm_yday in spring]
list_summer = [x for x in flat_list if x["date"].timetuple().tm_yday in summer]
list_fall = [x for x in flat_list if x["date"].timetuple().tm_yday in fall]
list_winter = [x for x in flat_list if x["date"].timetuple().tm_yday in winter]


        
user_count = {}
for x in data:
    user = x[0]['user']
    for y in x:
        if user != y['user']:
            raise Exception("User need to be the same over whole time")
    if user not in user_count:
        user_count[user] = 0
    user_count[user] += 1
max_user = sorted(user_count.items(), key=lambda x:x[1],reverse = True)
user_list = list(user_count.keys())

categories = get_categories(flat_list)
categories_spring = get_categories(list_spring)
categories_summer = get_categories(list_summer)
categories_fall = get_categories(list_fall)
categories_winter= get_categories(list_winter)
#plot somehow category differences for different meals

only_151 =  [x for x in flat_list if x['user'] == max_user[0][0]]
#ploot only_151 over one year

interaction = get_interaction(con,20)
interaction.sort(key=lambda x:x[1])
#plot interaction over one year

user_data = pd.DataFrame([get_user_info(con,x) for x in user_list])
food_data = pd.DataFrame(flat_list)
food_data = food_data.join(user_data.set_index('user'), on='user')

gender_nutries = []
meal_nutries = []
for nutri in ("calories","carbs","fat","protein", "cholest","sugar", "sodium", "fiber"):
    for gender in ("m","f"):
        x = food_data[food_data['gender']==gender][nutri]
        gender_nutries.append((np.mean(x),np.std(x)))
        
    for meal in ("breakfast","lunch","dinner","snacks"):    
        x = food_data[food_data['meal']==meal][nutri]
        meal_nutries.append((np.mean(x),np.std(x)))

#plot nutri per gender
#plot nutri per meal

