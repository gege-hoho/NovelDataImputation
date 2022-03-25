"""
Prints the percentage of users with an US state in there location
"""

from databaseConnector.databaseConnector import SqliteConnector
import pickle

whole_db = False
states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC",
          "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
          "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
          "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
          "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
          "VT", "VA", "WA", "WV", "WI", "WY"]
db = SqliteConnector("../preProcessor/data/mfp.db")

users = db.get_all_users_with_location()

if not whole_db:
    with open("../preProcessor/time_data_enorm.pickle", 'rb') as file:
        data = pickle.load(file)
    users_file = set([d[0]['user']for d in data])
    users = [u for u in users if u.id in users_file]
total_users = len(users)
c = 0
for x in users:
    loc = x.location.split(', ')
    loc = loc[-1]
    if len(loc) != 2:
        print(loc)
        continue
    if loc not in states:
        pass
        continue
        #print(loc)
    c += 1

print(c/total_users)



