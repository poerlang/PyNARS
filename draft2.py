"""
A draft for Markov stable distribution.
"""

import numpy as np
from scipy import linalg as lg

size = 100

mat = np.zeros((size, size))

for i in range(size):
    mat[i, i] = i / size
    if i != size - 1:
        mat[i, i + 1] = (size - i) / size
    else:
        mat[i, 0] = (size - i) / size

for each_A in mat:
    tmp = []
    for each_B in each_A:
        tmp.append(str(each_B))
    print(" ".join(tmp))
