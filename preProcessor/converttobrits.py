#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 11:14:04 2022

@author: gregor

Uses the exported data an convert it in a format for putting it into BRITS



"""
"""
cat_count = {}
for x in data:
    for y in x:
        l = len(set(y['category']))
        if l not in cat_count:
            cat_count[l] = 0
        cat_count[l] += 1
"""          
import pickle
from classifier import categories
import numpy as np
import math
import random

len_x_t = 9

def flatten(t):
    return [item for sublist in t for item in sublist]

file = open('time_data.pickle', 'rb')
data = pickle.load(file)
file.close()

vals= ['calories','carbs','fat','protein','cholest','sodium','sugar','fiber']
mean = {}
std = {}
for val in vals:
    cals = np.array(flatten([[y[val] for y in x]for x in data]))
    mean[val] = cals.mean()
    std[val] = math.sqrt(cals.std())


def parse_delta(masks, backward=False):
    if backward:
        masks = masks[::-1]

    deltas = []

    for h in range(len(masks)):
        if h == 0:
            deltas.append(np.ones(len_x_t))
        else:
            deltas.append(np.ones(len_x_t) + (1 - masks[h]) * deltas[-1])
    return np.array(deltas)

def convert_variable(curr_meal,var):
    #x = (float(curr_meal[var])-mean[var])/std[var]
    #y = x * std[var] + mean[var]
    #print(f"{curr_meal[var]}\n{y}")
    #print("")
    return (float(curr_meal[var])-mean[var])/std[var]

def convert_meal_to_brits(curr_meal,normalize):
    brits_day_data = []
    max_cat = 7 #if we only use 7 categories we have 95% of data included
    meal = 0
    if curr_meal['meal'] == 'breakfast':
        meal = 1
    elif curr_meal['meal'] == 'lunch':
        meal = 2
    elif curr_meal['meal'] == 'snacks':
        meal = 4
    elif curr_meal['meal'] == 'dinner':
        meal = 3
    else:
        raise Exception(f"Meal not detected {curr_meal[meal]}")
    
    #convert to category numbers
    daily_categories = [-1 for _ in range(max_cat)]
    for i,c in enumerate(curr_meal['category']):
        if i == max_cat:
            break
        daily_categories[i] = categories.index(c)
    daily_categories.sort(reverse=True)
    
    brits_day_data.append(meal)
    for val in vals:
        if normalize:
            brits_day_data.append(convert_variable(curr_meal,val))
        else:
            brits_day_data.append(curr_meal[val])
    #brits_day_data.extend(daily_categories)
    
    if len(brits_day_data) != len_x_t:
        raise Exception("len x_t divertes from what it should be!")
    return brits_day_data

def convert_series_to_brits(series,normalize=True):
    return np.array([convert_meal_to_brits(s,normalize) for s in series])
    
   
def convert_time_series(values,masks,deltas,evals,eval_masks):
    time_steps = []
    for i in range(len(evals)):
        entry = {
            'values': values[i].tolist(),
            'masks': masks[i].tolist(),
            'deltas':deltas[i].tolist(),
            'evals':evals[i].tolist(),
            'eval_masks':eval_masks[i].tolist()
            }
        time_steps.append(entry)    
    return time_steps

def build_brits(series,drop_meal_indices,normalize=True):
    evals = convert_series_to_brits(series,normalize=normalize)
    masks = np.ones((len(evals),len_x_t))
    eval_masks = np.zeros((len(evals),len_x_t))
    values = evals.copy()
    for index in drop_meal_indices:
        values[index] = np.zeros(len_x_t)
        masks[index] = np.zeros(len_x_t)
        eval_masks[index] = np.ones(len_x_t)
    
    deltas = parse_delta(masks)
    deltas_back = parse_delta(masks,backward =True)
    
    forwards = convert_time_series(values,masks,deltas,evals,eval_masks)
    backwards = convert_time_series(values[::-1],masks[::-1],deltas_back,evals[::-1],eval_masks[::-1])
    return {'forward': forwards,'backward': backwards}
    
folder = '../imputation/data'
    
with open(f'{folder}/brits_normalization.pickle','wb') as out:
    pickle.dump({'mean':mean,'std':std},out)


train = []
test = []

train_nonnorm = []
test_nonnorm =[]

train_only = False

random.seed(10)
for series in data:
    series = data[0]
    drop_meal_indices = np.random.choice(range(len(series)),len(series)//10)
    brits_nonnorm = build_brits(series,drop_meal_indices,normalize=False)
    brits_norm = build_brits(series,drop_meal_indices,normalize=True)
    if random.random() < 0.9 or train_only:
        train.append(brits_norm)
        train_nonnorm.append(brits_nonnorm)
    else:
        test.append(brits_norm)
        test_nonnorm.append(brits_nonnorm)

with open(f'{folder}/brits_test_nonnorm.pickle',"wb") as out:
    pickle.dump(test_nonnorm,out)

with open(f'{folder}/brits_test.pickle',"wb") as out:
    pickle.dump(test,out)
    
with open(f'{folder}/brits_train_nonnorm.pickle',"wb") as out:
    pickle.dump(train_nonnorm,out)

with open(f'{folder}/brits_train.pickle',"wb") as out:
    pickle.dump(train,out)

    