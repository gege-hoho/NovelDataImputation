#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 14:52:25 2022

@author: gregor
"""
import sqlite3
import datetime
import torch
from nltk.tokenize import RegexpTokenizer
from gensim.models import KeyedVectors
from gensim.models.phrases import Phrases, Phraser
import nltk
import numpy as np
import re

embedding_model = KeyedVectors.load("../preProcessor/data/models/mymodel")
embedding_size = 300
bigram_model = Phrases.load("../preProcessor/data/models/bigram_model.pkl")
bigram_model = Phraser(bigram_model)
nltk.download('stopwords')
nltk.download('wordnet')
lst_stopwords = nltk.corpus.stopwords.words("english")
custom = ["gal", "oz", "t", "tsp", "teaspoon", 
          "tablespoon", "tbl", "tbs", "tbsp",
          "fl", "oz", "gil", "ounce", "ml", "l",
          "dl", "lb", "pund", "mg", "g", "kg", "gram", "cup","cups","container","avg","homemade","piece","serving","spam","servings","grams"]
lst_stopwords.extend(custom)
tokenizer = RegexpTokenizer(r'\w+')
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

def embedd(tokens):
  embedding = np.zeros((10,embedding_size),dtype=float)
  for i,token in enumerate(tokens[:10]):
    if not(token == "" or token == " " or token not in embedding_model.wv):
      embedding[i,:] = embedding_model.wv[token]
  return torch.FloatTensor(embedding)

def preprocess(name):
    name = re.sub(r'[^\w\s]', '', str(name).lower().strip())
    name = tokenizer.tokenize(name)
    return [lemmatizer.lemmatize(x) for x in name if x not in lst_stopwords and len(x)>2 and not any(char.isdigit() for char in x)]

class FoodClassificationCnnModel(torch.nn.Module):
  def __init__(self, no_of_classes,device,dropout=0.2):
    super().__init__()
    n_filters = 100
    self.device = device
    self.no_of_classes = no_of_classes
    self.filter1 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (3, 300)).to(device)
    self.filter2 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (4, 300)).to(device) 
    self.filter3 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (5, 300)).to(device)
    self.filter4 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (1, 300)).to(device)
    self.linear = torch.nn.Sequential(torch.nn.Linear(4*n_filters,100),
                                      torch.nn.LeakyReLU(),
                                      torch.nn.BatchNorm1d(100),
                                      torch.nn.Linear(100,self.no_of_classes)).to(device)
    self.relu = torch.nn.ReLU().to(device)
    self.dropout = torch.nn.Dropout(dropout).to(device)
  
  def forward(self,x):
    x = x.unsqueeze(1)
    f1 = self.relu(self.filter1(x)).squeeze(3)
    f2 = self.relu(self.filter2(x)).squeeze(3)
    f3 = self.relu(self.filter3(x)).squeeze(3)
    f4 = self.relu(self.filter4(x)).squeeze(3)
    f1 = torch.nn.functional.max_pool1d(f1,f1.shape[2])
    f2 = torch.nn.functional.max_pool1d(f2,f2.shape[2])
    f3 = torch.nn.functional.max_pool1d(f3,f3.shape[2])
    f4 = torch.nn.functional.max_pool1d(f4,f4.shape[2])
    linear = self.dropout(torch.cat((f1,f2,f3,f4),dim=1)).squeeze(2)
    out = self.linear(linear)
    return out
    
  def get_accuracy(self,X,y):
    y_pred = self.forward(X)
    res = torch.argmax(y_pred, dim=1)
    res = y-res
    l = int(torch.count_nonzero(res))
    count = list(y_pred.shape)[0]
    return (count-l)/count

model = torch.load("../preProcessor/data/models/model93.2",map_location=torch.device('cpu'))
model.eval()

select_meal_history_filtered_by_user = """
select * from meal_history_flat mlf
where mlf.meal in ('breakfast','lunch','dinner','snacks') and 
mlf.name not like 'Quick Add%' and
mlf.user = ? and
exists (select * from (select sum(calories) s from meal_history_flat mlf2
                       where mlf2.user = mlf.user and mlf2.date = mlf.date and
                       mlf2.meal in ('breakfast','lunch','dinner','snacks')) a 
        where a.s > 1600)
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
select user from user 
where food_crawl_time is not null and 
exists(select * from meal_history_flat mlf where mlf.user = user)
"""

def get_meal_history_flat_filtered_by_user_id(con, user, snacks=True):
  cur = con.cursor()
  if snacks:
      cur.execute(select_meal_history_filtered_by_user , (user,))
  else:
      cur.execute(select_meal_history_filtered_by_user_no_snacks , (user,))
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

def get_user_ids_with_history(con):
    cur = con.cursor()
    cur.execute(select_user_with_history)
    res = cur.fetchall()
    res = [x[0] for x in res]
    return res

def extract_fragments_from_meals(meal_list):
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

x = embedd(bigram_model[preprocess("FRUIT WAVE".split(" "))]).float()
x = x.unsqueeze(0)
z = model.forward(x)

con = sqlite3.connect("../preProcessor/data/mfp.db")
user_ids = get_user_ids_with_history(con)
l = get_meal_history_flat_filtered_by_user_id(con, 9225,snacks=True)
fragments = extract_fragments_from_meals(l)

        
    
        
    