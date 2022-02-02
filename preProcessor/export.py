#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 14:52:25 2022

@author: gregor
"""
import sqlite3
import datetime
from classifier import FoodClassificationCnnModel,Classifier
import time
import json
import pickle

# Gets all meals for a user for days where there are mor than 1600 kcal and at least breakfast lunch and dinner
select_meal_history_filtered_by_user = """
select * from meal_history_flat mlf
where mlf.meal in ('breakfast','lunch','dinner','snacks') and
mlf.name not like 'Quick Add%' and
mlf.user = ? and
    exists (select * from meal_history_flat mlf3 where mlf3.date = mlf.date and mlf3.user = mlf.user and mlf3.meal = 'breakfast' and mlf3.name not like 'Quick Add%' ) and
    exists (select * from meal_history_flat mlf3 where mlf3.date = mlf.date and mlf3.user = mlf.user and mlf3.meal = 'lunch' and mlf3.name not like 'Quick Add%') and
    exists (select * from meal_history_flat mlf3 where mlf3.date = mlf.date and mlf3.user = mlf.user and mlf3.meal = 'dinner' and mlf3.name not like 'Quick Add%') and
    exists (select * from (select sum(calories) s from meal_history_flat mlf2
                       where mlf2.user = mlf.user and mlf2.date = mlf.date and
                       mlf2.meal in ('breakfast','lunch','dinner','snacks')) a
            where a.s > 1600);
"""

select_meal_history_filtered_by_user_no_snacks = """
select * from meal_history_flat mlf
where mlf.meal in ('breakfast','lunch','dinner','snacks') and
mlf.name not like 'Quick Add%' and
mlf.user = ? and not 
exists (select * from meal_history_flat mlf3 where mlf3.date = mlf.date and mlf3.user = mlf.user and mlf3.meal = 'snacks') and 
exists (select * from (select sum(calories) s from meal_history_flat mlf2
                       where mlf2.user = mlf.user and mlf2.date = mlf.date and
                       mlf2.meal in ('breakfast','lunch','dinner','snacks')) a
        where a.s > 1600)
"""

select_user_with_history = """
select u.user from user u
where u.food_crawl_time is not null and
exists(select * from meal_history_flat mlf where mlf.user = u.user) limit 10000
"""

def get_meal_history_flat_filtered_by_user_id(con, user, snacks=True):
  cur = con.cursor()
  if snacks:
      cur.execute(select_meal_history_filtered_by_user , (user,))
  else:
      cur.execute(select_meal_history_filtered_by_user_no_snacks , (user,))
  res = cur.fetchall()
  res = [{#'id': x[0],
          'date': datetime.datetime.strptime(x[1],'%d-%m-%y').date(),
          #'orig-date': x[1],
          'meal': x[2],
          'user': x[3],
          'name': x[4],
          #'quick_add': x[5],
          'calories': x[6],
          'carbs': x[7],
          'fat': x[8],
          'protein': x[9],
          'cholest': x[10],
          'sodium':x[11],
          'sugar': x[12],
          'fiber':x[13]
          } for x in res]
  cur.close()
  return res

def get_user_ids_with_history(con):
    cur = con.cursor()
    cur.execute(select_user_with_history)
    res = cur.fetchall()
    res = [x[0] for x in res]
    cur.close()
    return res

def extract_fragments_from_meals(meal_list):
    """Extract fragments from one users data where there are at least 7 days in a row and put
    them in fragments of 7 days"""
    fragment_size = 7 
    meal_list = meal_list.copy()
    meal_list.sort(key= lambda x: x['date'])
    datewise = {}
    for x in meal_list:
        curr_date = x['date']
        if curr_date not in datewise:
            datewise[curr_date] = []
        #x.pop('date')
        datewise[curr_date].append(x)
    
    user_fragments = []
    fragment_list = []
    last_date = datetime.date.min
    for curr_date,food_items in datewise.items():
        delta = curr_date-last_date
        if delta.days == 0:
            raise Exception("should not happen")
        if delta.days > 1:
            fragment_list = []
        last_date = curr_date
        fragment_list.append(food_items)
        if len(fragment_list) == fragment_size:
            user_fragments.append(fragment_list)
            fragment_list = []
            last_date = datetime.date.min
    return user_fragments

def classify_fragments(classy,fragments):
    """classifies the extracted fragments into food categories using a pretrained categoriser"""
    for x in fragments:  
        for meal_items in x:
            for meal_item in meal_items:
                if meal_item['name'] is None:
                    meal_item['category'] = None
                else:
                    meal_item['category'] = classy.get_cat_name(classy.classify(meal_item['name']))
    

def fill_up_empty_snacks(fragments):
    """creates an empty entry for snacks if no snacks are there. 
    All other meal types must exists"""
    for x in fragments:  
        for meal_items in x:
            if next((x for x in meal_items if x['meal'] == 'snacks'),None) is None:
                meal_items.append({'date': meal_items[0]['date'],
                                   'meal':'snacks',
                                   'user': meal_items[0]['user'],
                                   'name': None,
                                   'category': None,
                                   'calories': 0,
                                   'carbs': 0,
                                   'fat': 0,
                                   'protein': 0,
                                   'cholest': 0,
                                   'sodium':0,
                                   'sugar': 0,
                                   'fiber':0})
        
def process_fragments(classy,frags):
    """process the fragments and changes the frags variable"""
    classify_fragments(classy,frags)
    fill_up_empty_snacks(frags)

def combine(b):
    """combine all food items of one meal type by adding up the nutrients 
    and make a list of categories. We ignore everything that is None ergo 0 Imputation"""
    z = {'date': b[0]['date'],
         'meal':b[0]['meal'],
         'user': b[0]['user'],
         'category': [x['category'] for x in b if x['category'] is not None],
         'calories': sum([x['calories'] for x in b]),
         'carbs': sum([x['carbs'] for x in b if x['carbs'] is not None]),
         'fat': sum([x['fat'] for x in b if x['fat'] is not None]),
         'protein': sum([x['protein'] for x in b if x['protein'] is not None]),
         'cholest': sum([x['cholest'] for x in b if x['cholest'] is not None]),
         'sodium':sum([x['sodium'] for x in b if x['sodium'] is not None]),
         'sugar': sum([x['sugar'] for x in b if x['sugar'] is not None]),
         'fiber':sum([x['fiber'] for x in b if x['fiber'] is not None])}
    return z

def convert_to_time_series(frags):
    """Convert fragments into a time series data"""
    time_fragments = []
    for fragment in frags:
        user_fragment = []
        for day in fragment:
            user_fragment.append(combine([x for x in day if x['meal'] == 'breakfast']))
            user_fragment.append(combine([x for x in day if x['meal'] == 'lunch']))
            user_fragment.append(combine([x for x in day if x['meal'] == 'dinner']))
            user_fragment.append(combine([x for x in day if x['meal'] == 'snacks']))
        time_fragments.append(user_fragment)
    return time_fragments

with  open('time_data_big3.pickle', 'rb') as file:
   data = pickle.load(file) 
crawled_users = set([x[0]['user'] for x in data])

t0 = time.time()
classy = Classifier("../preProcessor")
con = sqlite3.connect("../preProcessor/data/mfp.db")
user_ids = get_user_ids_with_history(con)
time_series = data
for x in user_ids:
    if x <= max(crawled_users):
        continue
    print(f"Curr len: {len(time_series)} Now Processing: {x}")
    l = get_meal_history_flat_filtered_by_user_id(con, x,snacks=True)
    frags = extract_fragments_from_meals(l)
    process_fragments(classy,frags)
    time_series.extend(convert_to_time_series(frags))
    #if len(time_series) > 400:
    #    break
t1 = time.time()
print(f"TIme Elapsed {(t1-t0):2f}")
print(len(time_series))

with open('time_data_big4.pickle', 'wb') as outfile:
    pickle.dump(time_series, outfile)

#with open('data.json', 'w') as f:
#    json.dump(data, f)

