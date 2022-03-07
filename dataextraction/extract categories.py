#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  5 15:23:30 2022

@author: gregor

Create plots, that are based on the categories.
"""

import pickle
import datetime
import sqlite3
from tqdm import tqdm
import pandas as pd
from preProcessor.classifier import FoodClassificationCnnModel,Classifier,categories
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

con = sqlite3.connect("preProcessor/data/mfp.db")
classy = Classifier("preProcessor/data/models")
nutri_names = ("calories","carbs","fat","protein", "cholest","sugar", "sodium", "fiber")
meals = ["breakfast","lunch","dinner","snacks"]

font_size = 6.5
rcParams.update({'font.size':font_size})

plot_folder = 'dataextraction/plots/'

def save(fig,name):
    fig.tight_layout()
    plt.savefig(plot_folder+name) 


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

def get_meal_by_user_date(con,user,date):
    cur =  con.cursor()
    date = date.strftime('%d-%m-%y')
    cur.execute(f"""select * from meal_history_flat where user = {user} and date = '{date}'""")
    res = cur.fetchall()
    cur.close()   
    return [{"user": x[3],
      "meal": x[2],
      "date": x[1],
      "name": x[4],
      "calories": x[6],
      "carbs": x[7],
      "fat": x[8],
      "protein": x[9],
      "cholest":x[10],
      "sodium": x[11],
      "sugar": x[12],
      "fiber": x[13],
      "category":classy.get_cat_name(classy.classify(x[4]))}
     for x in res]

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

#remove values over 3000 cals
data = [series for series in data 
        if next((x for x in series if x['calories']>3000),None) == None]

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

categories_count = get_categories(flat_list)
selected_cats = ["Cereal","Milk","Bacon, Sausages & Ribs","Deli Salads",
                 "Meat/Poultry/Other Animals","Stuffing","Candy"]
cat_plot_arr = np.zeros((len(selected_cats),len(meals)))
for i,curr_cat in enumerate(selected_cats):
    meal_vals = [next((y for x,y in categories_count[m] if x==curr_cat),None)for m in meals]
    meal_vals = np.array(meal_vals)
    meal_vals = meal_vals/meal_vals.sum()
    cat_plot_arr[i] = meal_vals
cat_plot_arr = cat_plot_arr.transpose()

X = np.arange(len(selected_cats))
Y = np.arange(len(meals))
fig,axs = plt.subplots(nrows=1, ncols=1, figsize=(5.8, 3))
axs.set_xticks(X)
axs.set_xticklabels(selected_cats,rotation=45,rotation_mode="anchor",ha="left")
axs.set_yticks(Y)
axs.set_yticklabels(meals)
axs.xaxis.tick_top()
image = axs.imshow(cat_plot_arr,cmap="cividis")#viridis
divider = make_axes_locatable(axs)
cax = divider.append_axes("right", size="5%", pad=0.05)
fig.colorbar(image,cax=cax)
save(fig,"categories_to_meal_plot.pdf")

week_days=[[]for x in range(7)]



interaction = get_interaction(con,20)
interaction.sort(key=lambda x:x[1])
#todo: plot interaction over one year interaction

user_data = pd.DataFrame([get_user_info(con,x) for x in user_list])
food_data = pd.DataFrame(flat_list)
food_data = food_data.join(user_data.set_index('user'), on='user')

gender_nutries = []
meal_nutries = []

for nutri in nutri_names:
    for gender in ("m","f"):
        x = food_data[food_data['gender']==gender][nutri]
        gender_nutries.append((np.mean(x),np.std(x)))
        
    for meal in ("breakfast","lunch","dinner","snacks"):    
        x = food_data[food_data['meal']==meal][nutri]
        meal_nutries.append((np.mean(x),np.std(x)))

#todo: plot nutri per gender gender_nutries
#todo: plot nutri per meal meal_nutries
read_meals_from_db = False
if read_meals_from_db:
    meals = []
    food_data_no_duplicates = food_data[["date","user"]].drop_duplicates()
    for _,row in tqdm(food_data_no_duplicates.iterrows(),total=len(food_data_no_duplicates)):
        meals.extend(get_meal_by_user_date(con,row["user"],row["date"]))
    meal_df = pd.DataFrame(meals)
    with open('meals.pickle', 'wb') as file:
        pickle.dump(meal_df, file)    
else:
    with open('meals.pickle', 'rb') as file:
        meal_df = pickle.load(file)

meal_df = meal_df[meal_df["calories"]<2000]
meal_df = meal_df.join(user_data.set_index('user'), on='user')
meal_df["category"] = meal_df["category"].astype('category')
cat_wise_mean =  []
for cat in tqdm(categories):
    entry = {"category": cat}
    means = np.nanmean(meal_df[meal_df["category"] == cat][list(nutri_names)],0)
    stds = np.nanstd(meal_df[meal_df["category"] == cat][list(nutri_names)],0)
    for i,nutri in enumerate(nutri_names):
        entry[f"{nutri} mean"] = means[i]
        entry[f"{nutri} std"] = stds[i]
    cat_wise_mean.append(entry)
cat_wise_mean = pd.DataFrame(cat_wise_mean)
cat_wise_mean
#todo: plot cat_wise_mean
#why is std so high doesn't make sense to me???

meal_df[meal_df["gender"]=="m"]["category"].value_counts()[:10]
meal_df[meal_df["gender"]=="f"]["category"].value_counts()[:10]
#todo: plot category difference gender wise
    