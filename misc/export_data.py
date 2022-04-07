#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 11:55:16 2021

Export crawled data to file. Used for sanity checks in Jupyter Notebooks
@author: gregor
"""
import sys
sys.path.append("../crawler")

import csv
import argparse
from databaseConnector.databaseConnector import SqliteConnector


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract meals from users to csv')
    parser.add_argument('input', type=str, help='Path to database file')
    parser.add_argument('output', type=str, help='Path to outputfile')
    
    
    args = parser.parse_args()
    db = SqliteConnector(args.input)
    u1 = db.get_user_by_username('raeannvidal')
    u2 = db.get_user_by_username('Kathryn247')
    meal_history = db.get_meal_history_flat_by_user(u1)
    meal_history.extend(db.get_meal_history_flat_by_user(u2))
    
    with open(args.output, 'w', newline='') as csvfile:
        w = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        w.writerow(["meal", "meal_name"])
        for h in meal_history:
            w.writerow([h.meal,h.name])