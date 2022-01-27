#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 14 09:28:40 2021
Creates the csv thats given to the model in First Version of Jupyter Notebook
@author: gregor
"""
import pandas as pd
import csv
import numpy as np
import re
import nltk
from nltk.tokenize import RegexpTokenizer
from gensim.models import KeyedVectors
lst_stopwords = nltk.corpus.stopwords.words("english")
custom = ["gal", "oz", "t", "tsp", "teaspoon", 
          "tablespoon", "tbl", "tbs", "tbsp",
          "fl", "oz", "gil", "ounce", "ml", "l",
          "dl", "lb", "pund", "mg", "g", "kg", "gram", "cup","avg"]
lst_stopwords.extend(custom)
tokenizer = RegexpTokenizer(r'\w+')
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()


embedding_model = KeyedVectors.load("data/models/modelo3")
embedding_size = 300

not_listed = []

def embedd(tokens):
    embedding = np.zeros((embedding_size,))
    i = len(tokens)
    for token in tokens:
        if token not in embedding_model.wv:
            i -= 1
        else:
            embedding += embedding_model.wv[token]
    if i == 0:
        return None
    embedding = embedding/i
    return embedding

def preprocess2(name):
    name = re.sub(r'[^\w\s]', '', str(name).lower().strip())
    name = tokenizer.tokenize(name)
    name = [x for x in name if x not in lst_stopwords and len(x)>2]
    name = [x for x in name if not any(char.isdigit() for char in x)] 
    name = [lemmatizer.lemmatize(x) for x in name]
    return name

def preprocess(name):
    name = preprocess2(name)
    name = list(set(name))
    #todo bigrams
    return name

branded_food = pd.read_csv("data/branded_food.csv")
food2 = pd.read_csv("data/food.csv")
food2 = branded_food.merge(food2, on='fdc_id')
del branded_food
food = pd.DataFrame(food2["description"])
food["branded_food_category"] = food2["branded_food_category"].astype('category')
del food2


vc = food["branded_food_category"].value_counts()
vc = vc[vc > 100]
no_of_classes = len(vc)
food = food[food["branded_food_category"].isin(vc.index)]
food["branded_food_category"] = food["branded_food_category"].cat.remove_unused_categories()
food = food[~food["branded_food_category"].isnull()]
food["tokens"] = [preprocess(row) for row in food["description"]]
#food = food[~food["embedding"].isnull()]

X = list(food["tokens"])
y = food["branded_food_category"]

del food

with open('dataset.csv', 'w', newline='') as csvfile:
  w = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
  w.writerow(["category"]+ [f"token {i}" for i in range(10)])
  for x,curr_y in zip(X,y):
    l2 = ["" for i in range(10)]
    for i,curr_x in enumerate(x[:10]):
        l2[i]= curr_x
    l = [curr_y]
    l.extend(l2)
    w.writerow(l)

