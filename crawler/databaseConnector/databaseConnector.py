from datetime import datetime
import sqlite3

insert_into_user = "insert into user (username) values (?)"
select_uncrawled_friends_users = "select * from user where friends_crawl_time is NULL"
select_uncrawled_diaries_users = "select * from user where has_public_diary = 1 and food_crawl_time is NULL"
update_user = "update user set gender = ?, location = ?, joined_date = ?," \
              "food_crawl_time = ?, friends_crawl_time = ?, profile_crawl_time = ?," \
              "has_public_diary = ? where user = ?  "
does_user_exist = "select count(*) from user where username = ?"
get_meal_item = "select * from meal_item where name = ? and quick_add = ?"
insert_into_meal_item = "insert into meal_item (name, quick_add, calories, carbs, fat, protein, " \
                        "cholest, sodium, sugars, fiber) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

insert_into_meal_history = "insert into meal_history (user, meal_item, date, meal) values (?, ?, ?, ?)"

database_date_time_format = '%d-%m-%y %H:%M:%S'
database_date_format = '%d-%m-%y'


class User:
    def __init__(self, user_data):
        if len(user_data) != 9:
            raise Exception("length mismatch")
        self.id = user_data[0]
        self.username = user_data[1]
        self.gender = user_data[2]
        self.location = user_data[3]
        self.joined_date = datetime.strptime(user_data[4], database_date_format).date() if user_data[4] else None
        self.food_crawl_time = datetime.strptime(user_data[5], database_date_time_format) if user_data[5] else None
        self.friends_crawl_time = datetime.strptime(user_data[6], database_date_time_format) if user_data[6] else None
        self.profile_crawl_time = datetime.strptime(user_data[7], database_date_time_format) if user_data[7] else None
        self.has_public_diary = user_data[8]


class MealItem:
    def __init__(self, meal_data):
        if len(meal_data) != 11:
            raise Exception("length mismatch")
        self.id = meal_data[0]
        self.name = meal_data[1]
        self.quick_add = meal_data[2]
        self.calories = meal_data[3]
        self.carbs = meal_data[4]
        self.fat = meal_data[5]
        self.protein = meal_data[6]
        self.cholest = meal_data[7]
        self.sodium = meal_data[8]
        self.sugar = meal_data[9]
        self.fiber = meal_data[10]


class MealHistory:
    def __init__(self, meal_history_data):
        if len(meal_history_data) != 4:
            raise Exception("length mismatch")
        self.user = meal_history_data[0]
        self.meal_item = meal_history_data[1]
        self.date = meal_history_data[2]
        self.meal = meal_history_data[3]


class SqliteConnector:
    def __init__(self, db_name):
        """

        :param db_name: database used in the Sqlite connector
        :type db_name: str
        """
        self.con = sqlite3.connect(db_name)

    def exists_user(self, username, cur_cursor=None):
        cur_created = False
        if not cur_cursor:
            cur_cursor = self.con.cursor()
            cur_created = True
        cur_cursor.fetchall()
        cur_cursor.execute(does_user_exist, (username,))
        res = cur_cursor.fetchone()
        if cur_created:
            cur_cursor.close()
        return res[0] != 0

    def create_meal_history(self, user_id, meal_item_id, date, meal):
        """
        Creates a meal history for a user
        :param user_id:
        :type user_id: int
        :param meal_item_id:
        :type meal_item_id: int
        :param date: date of consumption
        :type date: datetime.datetime.date
        :param meal: b for breakfast, l lunch, d dinner, u unknown
        :type meal: str
        """
        date = date.strftime(database_date_format)
        cur = self.con.cursor()
        cur.execute(insert_into_meal_history, (user_id, meal_item_id, date, meal))
        cur.close()
        self.con.commit()

    def create_users(self, usernames):
        """
        Adds a bunch of crawled users to the Database
        :param usernames: List of usernames that should be added to the database
        :type usernames: list
        """
        cur = self.con.cursor()
        for username in usernames:
            if self.exists_user(username, cur_cursor=cur):
                continue
            self.con.execute(insert_into_user, (username,)).close()
        self.con.commit()
        cur.close()

    def create_meal_item(self, data):
        """
        Creates an meal item in the database
        :param data:
        :type data:
        """
        quick_add = 0
        name = data['name']
        # handle the MFP Quick Add functionality bc, the name has to be unique
        if "Quick Add - MyFitnessPal Premium" in data['name']:
            quick_add = 1
            name = "Quick Add"
            for key, x in data.items():
                if key == 'name':
                    continue
                x = x if x else "-"
                name += f" {x}"
        user_data = (name, quick_add, data['calories'],
                     data['carbs'], data['fat'], data['protein'],
                     data['cholest'], data['sodium'], data['sugars'], data['fiber'])
        self.con.execute(insert_into_meal_item, user_data).close()
        self.con.commit()
        return self.get_meal_item(name)

    def get_meal_item(self, name):
        """
        Gets a meal item by name if exists none otherwise
        :param name:
        :type name: str
        :return:
        :rtype: MealItem
        """
        cur = self.con.cursor()
        quick_add = 0
        if "Quick Add - MyFitnessPal Premium" in name:
            quick_add = 1
        cur.execute(get_meal_item, (name, quick_add))
        res = cur.fetchone()
        cur.close()
        if res:
            return MealItem(res)
        return None

    def get_uncrawled_friends_users(self):
        """
        Get list of users who does not have their friendlist crawled
        :return:
        :rtype: list of User
        """
        cur = self.con.execute(select_uncrawled_friends_users)
        result = cur.fetchall()
        result = [User(x) for x in result]
        cur.close()
        return result

    def get_uncrawled_diaries_users(self):
        """
        Get list of users who does not have their diaries crawled and have a diary available
        :return:
        :rtype: list of User
        """
        cur = self.con.execute(select_uncrawled_diaries_users)
        result = cur.fetchall()
        result = [User(x) for x in result]
        cur.close()
        return result

    def save_user(self, user):
        """
        Saves everything except the key and the username because they should not be immutable
        :param user:
        :type user: User
        """
        joined_date = user.joined_date
        if joined_date:
            joined_date = joined_date.strftime(database_date_format)

        food_crawl_time = user.food_crawl_time
        if food_crawl_time:
            food_crawl_time = food_crawl_time.strftime(database_date_time_format)

        friends_crawl_time = user.friends_crawl_time
        if friends_crawl_time:
            friends_crawl_time = friends_crawl_time.strftime(database_date_time_format)

        profile_crawl_time = user.profile_crawl_time
        if profile_crawl_time:
            profile_crawl_time = profile_crawl_time.strftime(database_date_time_format)

        user_data = (
            user.gender, user.location, joined_date, food_crawl_time,
            friends_crawl_time, profile_crawl_time, user.has_public_diary, user.id)
        self.con.execute(update_user, user_data).close()
        self.con.commit()