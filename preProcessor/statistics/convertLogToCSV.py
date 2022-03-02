#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 10:19:33 2022

@author: gregor
"""

import re

input_str = """
calories:
RNN    201.97061157226562
MEAN   229.93475341796875
MEANP  227.2735595703125
MEANM  220.7358856201172
carbs:
RNN    24.149776458740234
MEAN   29.719209671020508
MEANP  27.177289962768555
MEANM  28.983190536499023
fat:
RNN    10.245253562927246
MEAN   12.024554252624512
MEANP  11.88857364654541
MEANM  11.572504997253418
protein:
RNN    13.406362533569336
MEAN   17.43507957458496
MEANP  15.537017822265625
MEANM  16.38449478149414
"""

has_std = False

input_str = input_str.splitlines()
regex = r"\s{2,}(\S*)"
if has_std:
    regex = r"\((.*),(.*)\)"
    


border = ['calories:','carbs:','fat:','protein:']
out = []
curr_out = []
for x in input_str:
    if x == '':
        continue
    if x in border:
        if len(curr_out) > 0:
            out.append(curr_out)
            curr_out = []
        continue
    m = re.search(regex,x)
    mean = float(m.group(1))
    std = 0.0
    if has_std:
        std = float(m.group(2))
    curr_out.append((mean,std))
    
out.append(curr_out)

for i in range(len(curr_out)):
    if has_std:  
        s = ";".join([f"{x[i][0]:.2f} ({x[i][1]:.2f})"for x in out])
    else:
        s = ";".join([f"{x[i][0]:.2f} ()"for x in out])
    print(s)
        
        