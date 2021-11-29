from databaseConnector.databaseConnector import SqliteConnector
from helper.helper import read_json, get_unit_from_item_name
from preProcessor.categoryReader import read_categories, Category
from nltk.stem import WordNetLemmatizer
import nltk

from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
tokenizer = RegexpTokenizer(r'\w+')



def convert_to_categories(wiki_dict):
    categories = {}

    def read_recursive(sub, parent=None):
        for k, v in sub.items():
            if k not in categories:
                categories[k] = Category(k)
            if parent is not None:
                categories[k].add_parent(parent)
            read_recursive(v["sub-categories"], categories[k])
    read_recursive(wiki_dict)
    return categories


def get_all_category_tokens(intern_dict):
    ret = []
    for k in intern_dict:
        tok = tokenizer.tokenize(k.lower())
        tok = [lemmatizer.lemmatize(x) for x in tok if x not in stop_words]
        ret.append(tok)
    return ret


def export_tokens_from_meal_history(meal_history):
    all_tokens = {}
    for x in meal_history:
        units = get_unit_from_item_name(x.name)
        tokens = tokenizer.tokenize(units[0])
        tokens = [t for t in tokens if len(t) > 3]
        tokens = [lemmatizer.lemmatize(x.lower()) for x in tokens if not x.lower() in stop_words]
        for token in tokens:
            if token not in all_tokens:
                all_tokens[token] = 0
            all_tokens[token] += 1

    items = [i for i in all_tokens.items()]
    items.sort(key=lambda k: k[1], reverse=True)
    return items


wiki_cat = read_json("data/wiki_categories.json")
wiki_cat = convert_to_categories(wiki_cat)
tokens_names = get_all_category_tokens(wiki_cat)
db = SqliteConnector("../crawler/databaseConnector/mfp.db")
u1 = db.get_user_by_username('raeannvidal')
u2 = db.get_user_by_username('Kathryn247')
meal_history = db.get_meal_history_flat_by_user(u1)
meal_history.extend(db.get_meal_history_flat_by_user(u2))

result = []

for curr_meal in meal_history:
    units = get_unit_from_item_name(curr_meal.name)
    tokens = units[0].lower() + " " + (units[1].lower() if units[1] is not None else "")
    tokens = tokenizer.tokenize(tokens)
    tokens = [t for t in tokens if len(t) > 3]
    tokens = [lemmatizer.lemmatize(x) for x in tokens if x not in stop_words]
    matched = []
    for tk in tokens_names:
        if set(tk).issubset(tokens):
            matched.append(tk)
    result.append((curr_meal.name, matched))

empty = [x for x in result if x[1] == []]
print("result")


