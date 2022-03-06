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
from preProcessor.classifier import FoodClassificationCnnModel,Classifier,categories
import numpy as np
import math
import random


export_non_norm = False
export_categories = False
only_max_user = False
export_day = True
limit_data_per_user = 2
len_x_t = 10
time_data_file = 'preProcessor/time_data_big.pickle'
limit_top_categories = -1#30 #only take the most used x cateogries
max_cat = 7 #if we only use 7 categories we have 95% of data included
no_not_categories = 10
not_export_indexes = [0,9]#+list(range(no_not_categories,max_cat + no_not_categories))# indexes which shouldn't go missing (meal and categories)

def flatten(t):
    return [item for sublist in t for item in sublist]

with open(time_data_file, 'rb') as file:
    data = pickle.load(file)

data_categories = flatten([flatten([list(set(y['category'])) for y in x]) for x in data])
counted_categories = {}
for x in categories:
    if x not in counted_categories:
        counted_categories[x] = 0
    counted_categories[x] = data_categories.count(x)
counted_categories = sorted([x for x in counted_categories.items()], key=(lambda x:x[1]),reverse=True)
if limit_top_categories > 0:
    counted_categories = [x for x,_ in counted_categories][:limit_top_categories]

vals= ['calories','carbs','fat','protein','cholest','sodium','sugar','fiber']
mean = {}
std = {}
user_storage = {}

random.seed(10)
np.random.seed(10)

train_only = False
data_by_user= {}
if limit_data_per_user > 0:
    for x in data:
        user = x[0]['user']
        if user not in data_by_user:
            data_by_user[user] = []
        data_by_user[user].append(x)
    
    data_new = []    
    for v in data_by_user.values():
        if len(v) > limit_data_per_user:
            data_new.extend(random.sample(v,k=limit_data_per_user))
        else:
            data_new.extend(v)
data = data_new
"""    
data_new = []
for series in data:
    if limit_data_per_user > 0:
        user = series[0]['user']
        if user not in user_storage:
            user_storage[user] = 0
        if user_storage[user] >= limit_data_per_user:
            print(f"{user} is there to often skip")
            continue
        user_storage[user] += 1
    data_new.append(series)

data = data_new      
"""  

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
    return (float(curr_meal[var])-mean[var])/std[var]

def convert_meal_to_brits(curr_meal,normalize):
    brits_day_data = []
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
    if limit_top_categories > 0:
        cats = list(set([counted_categories.index(c) for c in curr_meal['category'] if c in counted_categories]))
    else:
        cats = list(set([categories.index(c) for c in curr_meal['category']]))
    for i,c in enumerate(cats):
        if i == max_cat:
            break
        daily_categories[i] = c
    daily_categories.sort(reverse=True)
    
    brits_day_data.append(meal)
    for val in vals:
        if normalize:
            brits_day_data.append(convert_variable(curr_meal,val))
        else:
            brits_day_data.append(curr_meal[val])
    if export_day:
        #print(curr_meal['date'].weekday())
        brits_day_data.append(curr_meal['date'].weekday())
    if export_categories:
        brits_day_data.extend(daily_categories)
    
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
        #now put meal back
        for x in not_export_indexes:
            values[index][x] = evals[index][x]
            masks[index][x] = 1
            eval_masks[index][x] = 0
    
    deltas = parse_delta(masks)
    deltas_back = parse_delta(masks,backward =True)
    
    forwards = convert_time_series(values,masks,deltas,evals,eval_masks)
    backwards = convert_time_series(values[::-1],masks[::-1],deltas_back,evals[::-1],eval_masks[::-1])
    return {'forward': forwards,'backward': backwards}
    
folder = 'imputation/data'
    
with open(f'{folder}/brits_normalization.pickle','wb') as out:
    pickle.dump({'mean':mean,'std':std},out)
print("Lets Go")

user_count = {}
for x in data:
    user = x[0]['user']
    for y in x:
        if user != y['user']:
            raise Exception("User need to be the same over whole time")
    if user not in user_count:
        user_count[user] = 0
    user_count[user] += 1

if only_max_user:
    max_user = sorted(user_count.items(), key=lambda x:x[1],reverse = True)
    max_user = max_user[49]
    #max_user = max_user[0]
    data = [s for s in data if s[0]['user'] == max_user[0]]
    random.seed(10)
    np.random.seed(10)
    #indexes = random.sample(range(len(data)),k=85)
    #data = [x for k,x in enumerate(data) if k in indexes]


random.seed(10)
np.random.seed(10)

train = []
test = []

train_nonnorm = []
test_nonnorm =[]

skip_over_cals = 3000 #skip week if it has over x calories
for series in data:
    drop_meal_indices = np.random.choice(range(len(series)),int(len(series)*0.1))
    brits_nonnorm = build_brits(series,drop_meal_indices,normalize=False)
    brits_norm = build_brits(series,drop_meal_indices,normalize=True)
    
    if next((x for x in series if x['calories']>skip_over_cals),None) != None:
        continue
    if random.random() < 0.9 or train_only:
        train.append(brits_norm)
        train_nonnorm.append(brits_nonnorm)
    else:
        test.append(brits_norm)
        test_nonnorm.append(brits_nonnorm)

print(len(train)+len(test))

with open(f'{folder}/brits_test.pickle',"wb") as out:
    pickle.dump(test,out)
with open(f'{folder}/brits_train.pickle',"wb") as out:
    pickle.dump(train,out)

if export_non_norm:  
    with open(f'{folder}/brits_train_nonnorm.pickle',"wb") as out:
        pickle.dump(train_nonnorm,out)
    with open(f'{folder}/brits_test_nonnorm.pickle',"wb") as out:
        pickle.dump(test_nonnorm,out)