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
      embedding = np.zeros((10,self.embedding_size),dtype=float)
      for i,token in enumerate(tokens[:10]):
        if not(token == "" or token == " " or token not in self.embedding_model.wv):
          embedding[i,:] = self.embedding_model.wv[token]
      return torch.FloatTensor(embedding)
    
    def preprocess(self,name):
        name = re.sub(r'[^\w\s]', '', str(name).lower().strip())
        name = self.tokenizer.tokenize(name)
        return [self.lemmatizer.lemmatize(x) for x in name if x not in self.lst_stopwords and len(x)>2 and not any(char.isdigit() for char in x)]

    def classify(self,word):
        x = self.embedd(self.bigram_model[self.preprocess(word)]).float()
        x = x.unsqueeze(0)
        z = self.model.forward(x)
        return torch.argmax(torch.nn.Softmax()(z))