#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 10:19:33 2022

@author: gregor
"""

import re

input_str = """
calories:
RNN    (220.03858947753906, 221.82608032226562)
MEAN   (268.01751708984375, 245.19027709960938)
MEANP  (262.71527099609375, 248.95050048828125)
MEANM  (254.31103515625, 231.03799438476562)

carbs:
RNN    (32.854732513427734, 35.40782165527344)
MEAN   (34.67216110229492, 37.2568473815918)
MEANP  (31.26945686340332, 35.198184967041016)
MEANM  (34.255088806152344, 36.918174743652344)

fat:
RNN    (10.690572738647461, 11.672393798828125)
MEAN   (13.590571403503418, 11.915566444396973)
MEANP  (12.895045280456543, 11.977263450622559)
MEANM  (13.06485366821289, 11.494646072387695)

protein:
RNN    (16.27105140686035, 14.018214225769043)
MEAN   (19.376028060913086, 15.400408744812012)
MEANP  (17.34624671936035, 15.054187774658203)
MEANM  (17.823034286499023, 14.665846824645996)
"""

has_std = True
print_std = False

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
    if print_std:  
        s = ";".join([f"{x[i][0]:.2f} ({x[i][1]:.2f})"for x in out])
    else:
        s = ";".join([f"{x[i][0]:.2f}"for x in out])
    print(s)
        
        