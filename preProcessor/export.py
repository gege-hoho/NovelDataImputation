#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 14:52:25 2022

@author: gregor
"""
import sqlite3
import datetime


select_meal_history_filtered_by_user = """
select * from meal_history_flat mlf
where mlf.meal in ('breakfast','lunch','dinner','snacks') and 
mlf.name not like 'Quick Add%' and
mlf.user = ? and
exists (select * from (select sum(calories) s from meal_history_flat mlf2
                       where mlf2.user = mlf.user and mlf2.date = mlf.date and
                       mlf2.meal in ('breakfast','lunch','dinner','snacks')) a 
        where a.s > 1200)
"""

select_meal_history_filtered_by_user_no_snacks = """
select * from meal_history_flat mlf
where mlf.meal in ('breakfast','lunch','dinner','snacks') and
mlf.name not like 'Quick Add%' and
mlf.user = 9225 and not 
    exists (select * from meal_history_flat mlf3 where mlf3.date = mlf.date and mlf3.user = mlf.user and mlf3.meal = 'snacks') and 
    exists (select * from (select sum(calories) s from meal_history_flat mlf2
                       where mlf2.user = mlf.user and mlf2.date = mlf.date and
                       mlf2.meal in ('breakfast','lunch','dinner','snacks')) a
            where a.s > 1200)
"""

select_user_with_history = """
select user from user 
where food_crawl_time is not null and 
exists(select * from meal_history_flat mlf where mlf.user = user)
"""

def get_meal_history_flat_filtered_by_user_id(con, user):
  cur = con.cursor()
  cur.execute(select_meal_history_filtered_by_user , (user,))
  res = cur.fetchall()
  res = [{#'id': x[0],
          'date': datetime.datetime.strptime(x[1],'%Y-%m-%d').date(),
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

def extract_fragments_from_meals(meal_list):
    meal_list = meal_list.copy()
    meal_list.sort(key= lambda x: x['date'])
    datewise = {}
    for x in meal_list:
        curr_date = x['date']
        if curr_date not in datewise:
            datewise[curr_date] = []
        x.pop('date')
        datewise[curr_date].append(x)
    
    user_fragments = []
    fragment_list = []
    fragment_size = 7 
    last_date = datetime.date.min
    for curr_date,food_items in datewise.items():
        delta = curr_date-last_date
        if delta.days == 0:
            raise Exception("should not happen")
        if delta.days > 1:
            fragment_list = []
        last_date = curr_date
        fragment_list.append((curr_date,food_items))
        if len(fragment_list) == fragment_size:
            user_fragments.append(fragment_list)
            fragment_list = []
            last_date = datetime.date.min
    return user_fragments

con = sqlite3.connect("../preProcessor/data/mfp.db")
l = get_meal_history_flat_filtered_by_user_id(con, 9225)
fragments = extract_fragments_from_meals(l)

        
    
        
    