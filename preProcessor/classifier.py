#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 11:05:42 2022

@author: gregor

Classifies the food item using a pretrained classifier, and embeddingmodel and bigrammodel
"""
import torch
from nltk.tokenize import RegexpTokenizer
from gensim.models import KeyedVectors
from gensim.models.phrases import Phrases, Phraser
import nltk
import numpy as np
import re
import time

categories = ['Alcohol',
 'Bacon, Sausages & Ribs',
 'Biscuits/Cookies',
 'Bread',
 'Breakfast Drinks',
 'Breakfast Sandwiches, Biscuits & Meals',
 'Candy',
 'Canned & Bottled Beans',
 'Canned Fruit',
 'Cereal',
 'Cereal/Muesli Bars',
 'Cheese',
 'Cheese/Cheese Substitutes',
 'Chewing Gum & Mints',
 'Chips, Pretzels & Snacks',
 'Chocolate',
 'Coffee',
 'Coffee/Tea/Substitutes',
 'Cooked & Prepared',
 'Cookies & Biscuits',
 'Cream',
 'Crusts & Dough',
 'Deli Salads',
 'Desserts/Dessert Sauces/Toppings',
 'Dips & Salsa',
 'Eggs & Egg Substitutes',
 'Energy, Protein & Muscle Recovery Drinks',
 'Entrees, Sides & Small Meals',
 'Fish & Seafood',
 'Flavored Rice Dishes',
 'French Fries, Potatoes & Onion Rings',
 'Frozen Breakfast Sandwiches, Biscuits & Meals',
 'Frozen Dinners & Entrees',
 'Frozen Fruit & Fruit Juice Concentrates',
 'Fruit  Prepared/Processed',
 'Fruit & Vegetable Juice, Nectars & Fruit Drinks',
 'Gelatin, Gels, Pectins & Desserts',
 'Grain Based Products / Meals',
 'Granulated, Brown & Powdered Sugar',
 'Gravy Mix',
 'Green Supplements',
 'Health Care',
 'Herbs & Spices',
 'Honey',
 'Ice Cream & Frozen Yogurt',
 'Iced & Bottle Tea',
 'Jam, Jelly & Fruit Spreads',
 'Ketchup, Mustard, BBQ & Cheese Sauce',
 'Liquid Water Enhancer',
 'Lunch Snacks & Combinations',
 'Meal Replacement Supplements',
 'Mexican Dinner Mixes',
 'Milk',
 'Milk Additives',
 'Other Condiments',
 'Other Deli',
 'Other Drinks',
 'Other Frozen Desserts',
 'Other Grains & Seeds',
 'Pancakes, Waffles, French Toast & Crepes',
 'Pasta Dinners',
 'Pasta/Noodles',
 'Pastry Shells & Fillings',
 'Pepperoni, Salami & Cold Cuts',
 'Pickles, Olives, Peppers & Relishes',
 'Pizza',
 'Pizza Mixes & Other Dry Dinners',
 'Plant Based Milk',
 'Plant Based Water',
 'Powdered Drinks',
 'Pre-Packaged Fruit & Vegetables',
 'Prepared Pasta & Pizza Sauces',
 'Prepared Soups',
 'Prepared/Preserved Foods Variety Packs',
 'Puddings & Custards',
 'Ready-Made Combination Meals',
 'Rice',
 'Salad Dressing & Mayonnaise',
 'Sauces/Spreads/Dips/Condiments',
 'Savoury Bakery Products',
 'Seasoning Mixes, Salts, Marinades & Tenderizers',
 'Snack, Energy & Granola Bars',
 'Soda',
 'Specialty Formula Supplements',
 'Sport Drinks',
 'Stuffing',
 'Sushi',
 'Sweet Bakery Products',
 'Syrups & Molasses',
 'Tea Bags',
 'Vegetable Based Products / Meals',
 'Vegetable and Lentil Mixes',
 'Vegetarian Frozen Meats',
 'Water',
 'Weight Control',
 'Yogurt',
 'Yogurt/Yogurt Substitutes',
 'Baking',
 'Cakes',
 'Soup',
 'Oils & Butters',
 'Dough Based Products',
 'Flours & Grains',
 'Meat/Poultry/Other Animals',
 'Non Alcoholic Beverages',
 'Cooking Sauces',
 'Subs, Sandwiches, Wraps & Burittos',
 'Vegetables']

print(__name__)

class FoodClassificationCnnModel(torch.nn.Module):
  def __init__(self, no_of_classes,device,dropout=0.2):
    super().__init__()
    n_filters = 100
    self.device = device
    self.no_of_classes = no_of_classes
    self.filter1 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (3, 300)).to(device)
    self.filter2 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (4, 300)).to(device) 
    self.filter3 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (5, 300)).to(device)
    self.filter4 =  torch.nn.Conv2d(in_channels = 1, 
                                    out_channels = n_filters, 
                                    kernel_size = (1, 300)).to(device)
    self.linear = torch.nn.Sequential(torch.nn.Linear(4*n_filters,100),
                                      torch.nn.LeakyReLU(),
                                      torch.nn.BatchNorm1d(100),
                                      torch.nn.Linear(100,self.no_of_classes)).to(device)
    self.relu = torch.nn.ReLU().to(device)
    self.dropout = torch.nn.Dropout(dropout).to(device)
  
  def forward(self,x):
    x = x.unsqueeze(1)
    f1 = self.relu(self.filter1(x)).squeeze(3)
    f2 = self.relu(self.filter2(x)).squeeze(3)
    f3 = self.relu(self.filter3(x)).squeeze(3)
    f4 = self.relu(self.filter4(x)).squeeze(3)
    f1 = torch.nn.functional.max_pool1d(f1,f1.shape[2])
    f2 = torch.nn.functional.max_pool1d(f2,f2.shape[2])
    f3 = torch.nn.functional.max_pool1d(f3,f3.shape[2])
    f4 = torch.nn.functional.max_pool1d(f4,f4.shape[2])
    linear = self.dropout(torch.cat((f1,f2,f3,f4),dim=1)).squeeze(2)
    out = self.linear(linear)
    return out
    
  def get_accuracy(self,X,y):
    y_pred = self.forward(X)
    res = torch.argmax(y_pred, dim=1)
    res = y-res
    l = int(torch.count_nonzero(res))
    count = list(y_pred.shape)[0]
    return (count-l)/count


class Classifier:
    def __init__(self, model_folder):
        self.model = torch.load(f"{model_folder}/model93.2",map_location=torch.device('cpu'))
        self.model.eval()
        self.embedding_model = KeyedVectors.load(f"{model_folder}/mymodel")
        self.embedding_size = 300
        bigram_model = Phrases.load(f"{model_folder}/bigram_model.pkl")
        self.bigram_model = Phraser(bigram_model)
        nltk.download('omw-1.4')
        nltk.download('stopwords')
        nltk.download('wordnet')
        self.lst_stopwords = nltk.corpus.stopwords.words("english")
        custom = ["gal", "oz", "t", "tsp", "teaspoon", 
                  "tablespoon", "tbl", "tbs", "tbsp",
                  "fl", "oz", "gil", "ounce", "ml", "l",
                  "dl", "lb", "pund", "mg", "g", "kg", "gram", "cup","cups","container","avg","homemade","piece","serving","spam","servings","grams"]
        self.lst_stopwords.extend(custom)
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
        
    def embedd(self,tokens):
        t0 = time.time()
        embedding = np.zeros((10,self.embedding_size),dtype=float)
        for i,token in enumerate(tokens[:10]):
            if not(token == "" or token == " " or token not in self.embedding_model.wv):
                embedding[i,:] = self.embedding_model.wv[token]
        res = torch.FloatTensor(embedding)
        #print(f"embedd:{time.time()-t0}")
        return res
    
    def preprocess(self,name):
        t0 = time.time()
        name = re.sub(r'[^\w\s]', '', str(name).lower().strip())
        name = self.tokenizer.tokenize(name)
        res = [self.lemmatizer.lemmatize(x) for x in name if x not in self.lst_stopwords and len(x)>2 and not any(char.isdigit() for char in x)]
        #print(f"preprocess:{time.time()-t0}")
        return res
    def get_cat_name(self,i):
        return categories[i]
    def classify(self,word):
        x = self.embedd(self.bigram_model[self.preprocess(word)]).float()
        x = x.unsqueeze(0)
        z = self.model.forward(x)
        return torch.argmax(torch.nn.Softmax(dim=1)(z))