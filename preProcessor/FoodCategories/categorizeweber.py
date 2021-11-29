#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 13:09:15 2021

@author: gregor
"""
import pandas as pd
import re
import nltk
from nltk.tokenize import RegexpTokenizer
tokenizer = RegexpTokenizer(r'\w+')

def preprocess(name):
   name = re.sub(r'[^\w\s]', '', str(name).lower().strip())
   name = tokenizer.tokenize(name)
   return name


crawled_food = pd.read_csv("data/crawled.csv")


with open("data/food_taxonomy.txt") as f:
    lines = f.readlines()

cats = []
for l in lines:
    l = l.lower().strip()
    l = l.split('\t')
    cats.append(l)

del lines
crawled_food["tokens"] = crawled_food.apply(lambda row: preprocess(row["meal_name"]), axis=1)
crawled_food["categories"] = crawled_food["tokens"].apply(lambda row: [x for x in cats if x[2] in row])
#crawled_food["categories"] = crawled_food["meal_name"].apply(lambda row: (" ".join(["{"+":".join(x)+"}" for x in cats if x[2] in preprocess(row)])))
#with pd.option_context('display.max_rows', None, 'display.max_columns', 100):
#    display(crawled_food[0:130][["meal_name","categories"]])

#"cucumber" in re.split("Cucumber, 1 cup, slices".lower())


