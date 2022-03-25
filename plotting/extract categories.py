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
import string
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

#remove values over 3000 cals
data = [series for series in data 
        if next((x for x in series if x['calories']>3000),None) == None]

flat_list = [item for sublist in data for item in sublist]
        
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
axs.set_xticklabels([x.lower() for x in selected_cats],rotation=45,rotation_mode="anchor",ha="left")
axs.set_yticks(Y)
axs.set_yticklabels(meals)
axs.xaxis.tick_top()
axs.set_xlabel("category")
axs.set_ylabel("meal")
image = axs.imshow(cat_plot_arr,cmap="cividis")#viridis
divider = make_axes_locatable(axs)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = fig.colorbar(image,cax=cax)
cbar.set_label('likelihood of category in meal', rotation=90)
save(fig,"categories_to_meal_plot.pdf")



week_days=[[]for x in range(7)]
for l in flat_list:
    week_days[l['date'].weekday()].append([l[n]for n in nutri_names])
week_days = np.array(week_days)
week_cals = week_days[:,:,0].mean(axis=1)*4
week_carbs = week_days[:,:,1].mean(axis=1)*4
week_carbs = week_carbs *4 #4 calories per 100g
week_fats = week_days[:,:,2].mean(axis=1)*4
week_fats = week_fats*9
week_protein = week_days[:,:,3].mean(axis=1)*4
week_protein = week_protein*4
week_sum = week_carbs +week_fats + week_protein
week_carbs = week_carbs/week_sum
week_fats = week_fats/week_sum
week_protein = week_protein/week_sum
#week_carbs = week_carbs/week_carbs.max()
#week_fats = week_fats/week_fats.max()
#week_protein = week_protein/week_protein.max()

X = np.arange(7)
fig,axs = plt.subplots(nrows=1, ncols=1, figsize=(5.8, 3.5))
axs2 = axs.twinx()
axs.set_ylabel("avg. calories")
axs2.plot(100*week_carbs,marker='s',label='carbs')
axs2.plot(100*week_fats,marker='s',label='fat')
axs2.plot(100*week_protein,marker='s',label='protein')
axs2.set_ylabel("avg. % of calories per nutrient")
axs.plot(week_cals)
axs.plot(week_cals,marker='o',color='gray',label='calories')
fig.legend()
axs.set_xticks(X)
axs.set_xticklabels(["mon","tue","wed","thu","fri","sat","sun"])
axs.set_xlabel("day of the week")
save(fig,"calories_nutrients_per_weekday_plot.pdf")



interaction = get_interaction(con,20)
interaction.sort(key=lambda x:x[1])

Y= [y for y,_ in interaction]
weekdays = [y for y,x in interaction if x.weekday()<5]
weekdays_X = [i for (i,(_,x)) in enumerate(interaction) if x.weekday()<5]
weekends = [y for y,x in interaction if x.weekday()>=5]
weekends_X = [i for (i,(_,x)) in enumerate(interaction) if x.weekday()>=5]
markers = [x.strftime("%b").lower() for _,x in interaction if x.day  == 1]
X = [i for i,(_,x) in enumerate(interaction) if x.day  == 1]
christmas = [y for y,x in interaction if x.day == x.day == 25 and x.month == 12]
christmas_X = [i for i,(_,x) in enumerate(interaction) if x.day == 25 and x.month == 12]
fig,axs = plt.subplots(nrows=1, ncols=1, figsize=(5.8, 1.5))
axs.plot(Y)
axs.plot(weekends_X,weekends,marker='s',markersize=1.5,label='weekend',linestyle="None")
axs.plot(christmas_X,christmas,marker='o',markersize=1.5,label='christmas',linestyle="None")
axs.set_xticks(X)
axs.set_xticklabels(markers)
axs.set_xlabel("day of the year 2020")
axs.set_ylabel("# of food entries")
axs.margins(x=0)
fig.legend()
save(fig,"interaction_plot.pdf")


user_data = pd.DataFrame([get_user_info(con,x) for x in user_list])
food_data = pd.DataFrame(flat_list)
food_data = food_data.join(user_data.set_index('user'), on='user')

gender_nutries = []
meal_nutries = []

for nutri in ("calories","carbs","fat","protein"):
    for gender in ("m","f"):
        x = food_data[food_data['gender']==gender][nutri]
        if nutri == "carbs":
            x = x*4
        elif nutri == "fat":
            x = x*9
        elif nutri == "protein":
            x = x*4
        gender_nutries.append((np.mean(x),np.std(x)))
        
    for meal in ("breakfast","lunch","dinner","snacks"):    
        x = food_data[food_data['meal']==meal][nutri]
        if nutri == "carbs":
            x = x*4
        elif nutri == "fat":
            x = x*9
        elif nutri == "protein":
            x = x*4
        meal_nutries.append((np.mean(x),np.std(x)))
gender_nutries = np.array(gender_nutries)
meal_nutries = np.array(meal_nutries)

fig,axs = plt.subplots(nrows=2, ncols=2, figsize=(5.8, 5))
X = np.arange(1)
for i in range(2):
    for k in range(2):
        if i + k == 0:
            continue
        axs[i,k].bar(X,100*gender_nutries[::2,0][2*i+k]/gender_nutries[0,0],width = 0.45, label = "male")
        axs[i,k].bar(X+0.45,100*gender_nutries[1::2,0][2*i+k]/gender_nutries[1,0],width = 0.45,label="female")
        axs[i,k].set_ylabel(f'% of {["calories","carbs","fat","protein"][2*i+k]} in calories')
        if k % 2 == 1:
            axs[i,k].yaxis.tick_right()
            axs[i,k].yaxis.set_label_position("right")
        axs[i,k].set_xticks([0,0.45])
        axs[i,k].set_xticklabels(["male","female"])
axs[0,0].bar(X,gender_nutries[0,0],width = 0.45, label = "male")
axs[0,0].bar(X+0.45,gender_nutries[1,0],width = 0.45,label="female")        
axs[0,0].set_ylabel("calories")
axs[0,0].set_xticks([0,0.45])
axs[0,0].set_xticklabels(["male","female"])
for n, ax in enumerate(axs.flatten()):
    ax.text(-0.1, 1.05, f"{string.ascii_lowercase[n]})", transform=ax.transAxes, 
            size=font_size)
save(fig,"nutrients_gender_plot.pdf")


fig,axs = plt.subplots(nrows=2, ncols=2, figsize=(5.8, 5))
X = np.arange(1)
for i in range(2):
    for k in range(2):
        if i + k == 0:
            continue
        axs[i,k].bar(X,100*meal_nutries[::4,0][2*i+k]/meal_nutries[0,0],width = 0.25)
        axs[i,k].bar(X+0.25,100*meal_nutries[1::4,0][2*i+k]/meal_nutries[1,0],width = 0.25)
        axs[i,k].bar(X+0.5,100*meal_nutries[2::4,0][2*i+k]/meal_nutries[2,0],width = 0.25)
        axs[i,k].bar(X+0.75,100*meal_nutries[3::4,0][2*i+k]/meal_nutries[3,0],width = 0.25)
        axs[i,k].set_ylabel(f'% of {["calories","carbs","fat","protein"][2*i+k]} in calories')
        if k % 2 == 1:
            axs[i,k].yaxis.tick_right()
            axs[i,k].yaxis.set_label_position("right")
        axs[i,k].set_xticks([0,0.25,0.5,0.75])
        axs[i,k].set_xticklabels(["breakfast","lunch","dinner","snacks"])
axs[0,0].bar(X,meal_nutries[0,0],width = 0.25)
axs[0,0].bar(X+0.25,meal_nutries[1,0],width = 0.25)
axs[0,0].bar(X+0.5,meal_nutries[2,0],width = 0.25)
axs[0,0].bar(X+0.75,meal_nutries[3,0],width = 0.25)
axs[0,0].set_ylabel("calories")
axs[0,0].set_xticks([0,0.25,0.5,0.75])
axs[0,0].set_xticklabels(["breakfast","lunch","dinner","snacks"])
for n, ax in enumerate(axs.flatten()):
    ax.text(-0.1, 1.05, f"{string.ascii_lowercase[n]})", transform=ax.transAxes, 
            size=font_size)
save(fig,"nutrients_meal_plot.pdf")

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
selected_cat_wise_mean = cat_wise_mean[cat_wise_mean["category"].isin(selected_cats)]
scwm = np.zeros((7,4))
for i,k in enumerate(selected_cats):
    row = selected_cat_wise_mean[selected_cat_wise_mean["category"]==k]
    scwm[i,:] = row[["calories mean","carbs mean","fat mean", "protein mean"]]
    
#scwm = np.array(selected_cat_wise_mean[["calories mean","carbs mean","fat mean", "protein mean"]])
scwm = scwm*[1,4,9,4]
scwm = scwm.transpose()
w= 1.0/scwm.shape[1]


fig,axs = plt.subplots(nrows=1, ncols=1, figsize=(5.8, 3))
X = np.arange(1)
for j,row in enumerate(scwm[0]):
    axs.bar(X+j*w,row,width = w )
axs.set_ylabel("calories")
axs.set_xticks([i*w for i in range(len(selected_cats))])
axs.set_xlabel("category")
axs.set_xticklabels([x.lower() for x in selected_cats],rotation=45,rotation_mode="anchor",ha="right")
save(fig,"calories_selected_categories_plot.pdf")

X = np.arange(len(selected_cats))
Y = np.arange(3)

fig,axs = plt.subplots(nrows=1, ncols=1, figsize=(5.8, 2.5))
axs.set_xticks(X)
axs.set_xticklabels([x.lower() for x in selected_cats],rotation=45,rotation_mode="anchor",ha="left")
axs.set_yticks(Y)
axs.set_yticklabels(["carbs","fat","protein"])
axs.set_xlabel("category")
axs.set_ylabel("nutrient")
axs.xaxis.tick_top()
image = axs.imshow(scwm[1:,:]/scwm[0,:],cmap="cividis")#viridis
divider = make_axes_locatable(axs)
cax = divider.append_axes("right", size="5%", pad=0.05)
cbar = fig.colorbar(image,cax=cax)
cbar.set_label('caloriewise % \n of nutrient in portion', rotation=90)
save(fig,"nutrition_distribution_categories_plot.pdf")


meal_df[meal_df["gender"]=="m"]["category"].value_counts()[:10]
meal_df[meal_df["gender"]=="f"]["category"].value_counts()[:10]
#todo: plot category difference gender wise
    