#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 11:14:04 2022

@author: gregor

Uses the exported data an convert it in a format for putting it into BRITS



"""
import pickle
from classifier import categories
import numpy as np
import math
import random
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert full weeks to BRITS and create artificial gaps')
    parser.add_argument('input', type=str, help='Pickle file used as input')
    parser.add_argument('output', type=str, help='Folderpath were to put the output files')
    parser.add_argument('--user_id', nargs='?', default=-1, type=int,
                         help='Only weeks of a specific user-id are extracted or -1 (default)')
    parser.add_argument('--non_norm', nargs='?', default=False, type=bool,
                         help='If true export as non normalized')
    parser.add_argument('--max_cat', nargs='?', default=0, type=int,
                         help='Number of categories to be exported per sequence entry or 0 (default)')
    parser.add_argument('--only_max_user', nargs='?', default=False, type=bool,
                         help='If true only entries of the user with the most entries is exported')
    parser.add_argument('--limit_data_per_user', nargs='?', default=-1, type=int,
                         help='Max number of weeks for one user exported or -1 for unlimited (default)')
    parser.add_argument('--missing', nargs='?', default=0.1, type=float,
                         help='Percentage of missing meals 0.1(default)')
    parser.add_argument('--train', nargs='?', default=0.9, type=float,
                         help='Percentage of meals in train set 0.9(default)')
    parser.add_argument('--limit_categories', nargs='?', default=30, type=int,
                         help='only take the most used x cateogries (default 30)')
    parser.add_argument('--skip_over_cals', nargs='?', default=-1, type=int,
                         help='skip weeks with meals over x calories or -1 (default)')
    args = parser.parse_args()

    export_user_id = args.user_id
    export_non_norm = args.non_norm
    time_data_file = args.input
    folder = args.output
    max_cat = args.max_cat #if we only use 7 categories we have 95% of data included
    only_max_user = args.only_max_user
    limit_data_per_user = args.limit_data_per_user
    
    
    missing_percentage = args.missing
    train_percentage = args.train #amount of data should go to train set
    skip_over_cals = args.skip_over_cals #skip week if it has over x calories
    limit_top_categories = args.limit_categories
   
    no_not_categories = 10
    not_export_indexes = [0,9]#+list(range(no_not_categories,max_cat + no_not_categories))# indexes which shouldn't go missing (meal and categories) 
    len_x_t = max_cat + no_not_categories


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
#vals= ['calories','carbs','fat','protein']
mean = {}
std = {}
user_storage = {}

random.seed(10)
np.random.seed(10)

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
    brits_day_data.append(curr_meal['date'].weekday())      
    if max_cat > 0:
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
    
if __name__ == '__main__':
    
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
        max_user = max_user[0]
        data = [s for s in data if s[0]['user'] == max_user[0]]
    if export_user_id != -1:
        data = [s for s in data if s[0]['user'] == export_user_id]
        
    
    
    random.seed(10)
    np.random.seed(10)
    
    train = []
    test = []
    
    train_nonnorm = []
    test_nonnorm =[]
    
    
    for series in data:
        drop_meal_indices = np.random.choice(range(len(series)),int(len(series)*missing_percentage))
        brits_nonnorm = build_brits(series,drop_meal_indices,normalize=False)
        brits_norm = build_brits(series,drop_meal_indices,normalize=True)
        
        if skip_over_cals != -1 and next((x for x in series if x['calories']>skip_over_cals),None) != None:
            continue
        if random.random() < train_percentage:
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