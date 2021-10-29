import logging

from databaseConnector.databaseConnector import SqliteConnector, database_date_time_format
from helper.helper import read_json, convert_int
from helper.timer import Timer

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                    datefmt=database_date_time_format,
                    handlers=[
                        logging.StreamHandler()
                    ],
                    level=logging.getLevelName("DEBUG"))

config = read_json("config.json")
db = SqliteConnector(config["database-path"])
meal_items = db.get_meal_items_limited(416832)
#meal_items = meal_items[169:]  # skip for now
t = Timer()
t.tick()
meal_items = meal_items.sort(key=(lambda k: k.name))
t.tock("blaa")


def detector(string):
    string = string.split(' ', 1)
    number = convert_int(string[0])
    # if this doesn't work try with eval e.g for 5/3
    if number is None:
        try:
            number = eval(string[0])
        except:
            return None
        if type(number) not in (int, float):
            return None
    unit = None
    if len(string) == 2:
        unit = string[1]
    return number, unit


def get_unit_from_item_name(name):
    name_split = name.split(', ')
    curr = ""
    for split in reversed(name_split):

        curr = split if curr == "" else split + ', ' + curr
        result = detector(curr)
        if result is not None:
            return name.rstrip(curr).rstrip(','), result
    return None


for item in meal_items:
    x = get_unit_from_item_name(item.name)
    print(f"{x[1][0]}")
    if x is None:
        print(item.name)
