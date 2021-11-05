import logging

from databaseConnector.databaseConnector import SqliteConnector, database_date_time_format, MealItem
from helper.helper import read_json, convert_int, isclose
from helper.timer import Timer

logging.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s',
                    datefmt=database_date_time_format,
                    handlers=[
                        logging.StreamHandler()
                    ],
                    level=logging.getLevelName("DEBUG"))
attr_list = ['calories', 'carbs', 'fat', 'protein', 'cholest', 'sodium', 'sugar', 'fiber']

def both_or_no_one_none(a, b):
    return (a is None and b is None) or (a is not None and b is not None)


def compare_with_multiplier(multiplier, reference: MealItem, compare_list: [(int,str,MealItem)]):

    for comp_unit, _, compare in compare_list:
        for attr in attr_list:
            # check if all relevant attributes (carbs, calories,...) from the class are at the same thing none
            cur_ref = getattr(reference, attr)
            cur_comp = getattr(compare, attr)
            if cur_ref is None and cur_comp is None:
                continue
            if multiplier == 0 or comp_unit == 0:
                if multiplier == comp_unit:
                    continue
                logging.info("Not possible to match %s because One Multiplier is Zero", reference.name)
                return False
            if cur_ref is not None and cur_comp is not None:
                if not isclose(cur_ref/multiplier, cur_comp/comp_unit):
                    logging.info("Not possible to match %s for %s because %.2f is not close enough to %.2f",
                                 reference.name, attr, cur_ref/multiplier, cur_comp/comp_unit)
                    return False
            else:
                logging.info("Not possible to match %s for %s because one is None", reference.name, attr)
                return False

config = read_json("config.json")
db = SqliteConnector(config["database-path"], 0, 0)
meal_items = db.get_meal_items_limited(416832)
#meal_items = meal_items[169:]  # skip for now
t = Timer()
meal_items.sort(key=(lambda k: k.name))
matched_items = {}
t.tick()
for item in meal_items:
    x_name, (x_amt, x_unit) = get_unit_from_item_name(item.name)
    if x_name not in matched_items:
        matched_items[x_name] = []
    matched_items[x_name].append((x_amt, x_unit, item))
t.tock("Matching took")
logging.info("")
fail = 0

matched_items_no_single = {}
for k, v in matched_items.items():
    if len(v) > 1:
        matched_items_no_single[k] = v

for x in matched_items_no_single.values():
    if len(x) <= 1:
        continue
    ref = x[0][2]
    ref_amt = x[0][0]
    if not compare_with_multiplier(ref_amt, ref, x):
        fail += 1

logging.info("Fail: %i Suc: %i", fail, len(matched_items_no_single)-fail)
