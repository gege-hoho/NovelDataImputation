#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 14:25:19 2022

@author: gregor
"""

import sqlite3
from preProcessor.classifier import FoodClassificationCnnModel,Classifier
import numpy as np
import matplotlib.pyplot as plt

plot_folder = 'dataextraction/plots/'

def get_user_numbers(con):
    cur = con.cursor()
    cur.execute("""select * from
(select count(*) from user) all_u,
(select count(*) from user where has_public_diary = 1),
(select count(*) from user where food_crawl_time is not null) all_crawled
""")
    res = cur.fetchall()
    #res = [x[0] for x in res]
    cur.close()
    return res[0]


clauses = ["1=1","has_public_diary = 1","has_public_diary = 0"]#
def get_gender(con):
    res = []
    for x in clauses:
        sql = f"select gender, count(*) from user where {x} group by gender"
        cur = con.cursor()
        cur.execute(sql)
        curr = cur.fetchall()
        print(curr)
        res.append([x for _,x in curr])
        cur.close()
    return res

def get_age(con):
    res = []
    for x in clauses:
        sql = f"select age, count(*) from user where {x} group by age"
        cur = con.cursor()
        cur.execute(sql)
        curr = cur.fetchall()
        print(curr)
        res.append(curr)
        cur.close()
    new_ages = []
    for group in res:
        curr = np.zeros(6)
        for age,age_nos in group:
            if age == None:
                #curr[6] += age_nos
                print(f"Found {age_nos} in None age")
            elif age <= 19:
                curr[0] += age_nos
            elif age <= 29:
                curr[1] += age_nos
            elif age <= 39:
                curr[2] += age_nos
            elif age <= 49:
                curr[3] += age_nos
            elif age <= 59:
                curr[4] += age_nos
            else:
                curr[5] += age_nos
        new_ages.append(curr)
    return np.array(new_ages)

def get_gender_age(con):
    res = []
    for x in clauses:
        sql = f"select gender, age, count(*) from user where {x} group by age, gender"
        cur = con.cursor()
        cur.execute(sql)
        curr = cur.fetchall()
        print(curr)
        res.append(curr)
        cur.close()
    new_ages = []
    for group in res:
        curr = np.zeros((3,6))
        for gender,age,age_nos in group:
            #convert gender to offset
            if gender == 'f':
                gender = 1
            elif gender == 'm':
                gender = 2
            else:
                gender = 0
            if age == None:
                print(f"Found {age_nos} in None age")
            elif age <= 19:
                curr[gender,0] += age_nos
            elif age <= 29:
                curr[gender,1] += age_nos
            elif age <= 39:
                curr[gender,2] += age_nos
            elif age <= 49:
                curr[gender,3] += age_nos
            elif age <= 59:
                curr[gender,4] += age_nos
            else:
                curr[gender,5] += age_nos
        new_ages.append(curr)
    return np.array(new_ages)

classy = Classifier("preProcessor/data/models")
con = sqlite3.connect("preProcessor/data/mfp.db")
nos = np.array(get_user_numbers(con))
print(f"Total accounts: {nos[0]}")
print(f"Total public accounts: {nos[1]}")
print(f"Total crawled public accounts {nos[2]}")

gender_nos = np.array(get_gender(con)).transpose()
gender_nos = (gender_nos*1.0)/gender_nos.sum(0) #get relative values
gender_nos = gender_nos.transpose()

ages = get_age(con)
ages = (ages.transpose()/ages.sum(1)).transpose()

gender_ages = get_gender_age(con)

print("Age groups not many people reported age!!")
X = np.arange(6)
fig = plt.figure()
#fig, (ax1, ax2) = plt.subplots(1, 2)
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.set_title("Age Comparison for public diary")
ax1.set_xticks(X+0.25)
ax1.set_xticklabels(["<20", "20-29","30-39","40-49","50-59","60+"])
ax1.bar(X + 0.00, ages[0], color = 'b', width = 0.25)
ax1.bar(X + 0.25, ages[1], color = 'g', width = 0.25)
ax1.bar(X + 0.50, ages[2], color = 'r', width = 0.25)
ax1.legend(["Total","Public Diary","Private Diary"])
plt.savefig(plot_folder+"age_group_plot.pdf") 

X = np.arange(3)
fig = plt.figure()
#fig, (ax1, ax2) = plt.subplots(1, 2)
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.set_title("Gender Comparison for public diary")
ax1.set_xticks(X+0.25)
ax1.set_xticklabels(["N/A", "Female","Male"])
ax1.bar(X + 0.00, gender_nos[0], color = 'b', width = 0.25)
ax1.bar(X + 0.25, gender_nos[1], color = 'g', width = 0.25)
ax1.bar(X + 0.50, gender_nos[2], color = 'r', width = 0.25)
ax1.legend(["Total","Public Diary","Private Diary"])
plt.savefig(plot_folder+"gender_plot.pdf") 

X = np.arange(3)
fig = plt.figure()
#fig, (ax1, ax2) = plt.subplots(1, 2)
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.set_title("Comparison of crawled data")
ax1.set_xticks(X)
ax1.set_xticklabels(["All","Public Diary","Crawled Diary"])
ax1.bar(X + 0.00, nos, color = 'b', width = 0.9)
plt.savefig(plot_folder+"crawled_plot.pdf") 

def plot_gender_ages(curr_gender_ages,title,ax1):
    X = np.arange(6)

    ax1.set_title(title)
    ax1.set_xticks(X+0.25)
    ax1.set_xticklabels(["<20", "20-29","30-39","40-49","50-59","60+"])
    ax1.bar(X + 0.00, curr_gender_ages[0], color = 'b', width = 0.25)
    ax1.bar(X + 0.25, curr_gender_ages[1], color = 'g', width = 0.25)
    ax1.bar(X + 0.50, curr_gender_ages[2], color = 'r', width = 0.25)
    ax1.legend(["N/A", "Female","Male"])


fig,ax = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))
plot_gender_ages(gender_ages[0],"Gender to Agegroup plot",ax[0])
plot_gender_ages(gender_ages[1],"Gender to Agegroup plot with public diary",ax[1])
plot_gender_ages(gender_ages[2],"Gender to Agegroup plot with cralwed diary",ax[2])
plt.savefig(plot_folder+"gender_age_plot.pdf",pad_inches=0) 





