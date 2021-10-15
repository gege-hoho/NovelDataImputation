import argparse
import sqlite3

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create Database')
    parser.add_argument('-db',dest='db_path',
                        help='Path were the Databasefile should be created')
    parser.add_argument('-script',dest='db_script_path',
                        help='Path were the SQL script is located')
    args = parser.parse_args()

    con = sqlite3.connect(args.db_path)
    sql_file = open(args.db_script_path, 'r')
    cur = con.cursor()
    cur.executescript(sql_file.read())
    cur.close()
    con.close()
    sql_file.close()

