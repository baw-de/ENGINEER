# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 08:49:15 2026

@author: belzner
"""

import STL_function

D = 0.5
W = 4
alpha = 8
t = 0.7
B = 10
B -= t
P = 6

filename = 'labyrinth_stl.stl'

STL_function.generate_labyrinth_geometry(D, W, alpha, B, t, P, filename)
