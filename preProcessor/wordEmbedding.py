#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 17:26:19 2021

@author: gregor
"""
from gensim.models import KeyedVectors
import nltk
from nltk.tokenize import RegexpTokenizer
import pandas as pd
import numpy as np
import re
from sklearn import feature_extraction, model_selection, naive_bayes, pipeline, manifold, preprocessing

lst_stopwords = nltk.corpus.stopwords.words("english")
custom = ["gal", "oz", "t", "tsp", "teaspoon", 
          "tablespoon", "tbl", "tbs", "tbsp",
          "fl", "oz", "gil", "ounce", "ml", "l",
          "dl", "lb", "pund", "mg", "g", "kg"]
lst_stopwords.extend(custom)
tokenizer = RegexpTokenizer(r'\w+')
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

model = KeyedVectors.load("data/models/v2/modelo3")
embedding_size = 300

not_listed = []

def embedd(tokens):
    embedding = np.zeros((embedding_size,))
    i = len(tokens)
    for token in tokens:
        if token not in model.wv:
            #not_listed.append(token)
            i -= 1
        else:
            embedding += model.wv[token]
    if i == 0:
        #print(f"could not embedd {tokens}")
        return None
    embedding = embedding/i
    return embedding
    

def preprocess(name):
    name = re.sub(r'[^\w\s]', '', str(name).lower().strip())
    name = tokenizer.tokenize(name)
    name = [x for x in name if x not in lst_stopwords]
    name = [x for x in name if not x.isnumeric()] 
    name = [lemmatizer.lemmatize(x) for x in name]
    name = list(set(name))
    #todo bigrams
    return name


food = None
branded_food = pd.read_csv("data/branded_food.csv")
food = pd.read_csv("data/food.csv")
food = branded_food.merge(food, on='fdc_id')
del branded_food
# print no of cateogries
print(len(food.branded_food_category.unique()))
food["tokens"] = food.apply(lambda row: preprocess(row["description"]), axis=1)

print("tokenized now lets go to embedding")
#todo check if any tokens have 0 embedding
food["embedding"] = food.apply(lambda row: embedd(row["tokens"]),axis=1)

print("embedded")

#filter things with 0 embedding
food = food[~food["embedding"].isnull()]

