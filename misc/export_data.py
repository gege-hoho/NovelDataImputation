#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 11:55:16 2021

Export crawled data to file. Used for sanity checks in Jupyter Notebooks
@author: gregor
"""
import csv
from databaseConnector.databaseConnector import SqliteConnector

db = SqliteConnector("databaseConnector/mfp.db")
u1 = db.get_user_by_username('raeannvidal')
u2 = db.get_user_by_username('Kathryn247')
meal_history = db.get_meal_history_flat_by_user(u1)
meal_history.extend(db.get_meal_history_flat_by_user(u2))

with open('crawled.csv', 'w', newline='') as csvfile:
    w = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    w.writerow(["meal", "meal_name"])
    for h in meal_history:
        w.writerow([h.meal,h.name])