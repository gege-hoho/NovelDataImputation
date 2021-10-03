import sqlite3

insert_into_user = "insert into user (username) values (?)"
select_uncrawled_friends_users = "select * from user where friends_crawl_time is NULL"
update_user = "update user set gender = ?, location = ?, joined_date = ?," \
              "food_crawl_time = ?, friends_crawl_time = ?, profile_crawl_time = ?," \
              "has_public_diary = ? where user = ?  "
does_user_exist = "select count(*) from user where username = ?"


class User:
    def __init__(self, user_data):
        if len(user_data) != 9:
            raise Exception("length mismatch")
        self.id = user_data[0]
        self.username = user_data[1]
        self.gender = user_data[2]
        self.location = user_data[3]
        self.joined_date = user_data[4]
        self.food_crawl_time = user_data[5]
        self.friends_crawl_time = user_data[6]
        self.profile_crawl_time = user_data[7]
        self.has_public_diary = user_data[8]


class SqliteConnector:
    def __init__(self, db_name):
        """

        :param db_name: database used in the Sqlite connector
        :type db_name: str
        """
        self.con = sqlite3.connect(db_name)

    def exists_user(self, username, cur=None):
        cur_created = False
        if not cur:
            cur = self.con.cursor()
            cur_created = True
        cur.fetchall()
        cur.execute(does_user_exist, (username,))
        res = cur.fetchone()
        if cur_created:
            cur.close()
        return res[0] != 0

    def create_users(self, usernames):
        """
        Adds a bunch of crawled users to the Database
        :param usernames: List of usernames that should be added to the database
        :type usernames: list
        """
        cur = self.con.cursor()
        for username in usernames:
            if self.exists_user(username, cur=cur):
                continue
            self.con.execute(insert_into_user, (username,))
        self.con.commit()
        cur.close()

    def get_uncrawled_friends_users(self):
        """

        :return:
        :rtype: list of User
        """
        cur = self.con.execute(select_uncrawled_friends_users)
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
        user_data = (
            user.gender, user.location, user.joined_date, user.food_crawl_time, user.friends_crawl_time,
            user.profile_crawl_time, user.has_public_diary, user.id)
        self.con.execute(update_user, user_data).close()
        self.con.commit()
