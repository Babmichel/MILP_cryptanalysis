import numpy as np
from sage.all import Matrix, GF

lambda0= np.array([
[1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
[0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
[1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
[0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0],
[0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1]
])
lambda1 = np.array([
[1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
[0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1]])

lambda2 = np.array([
[1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
[0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
[0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
[0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
[1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
[0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0],
[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1],
[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0],
[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1]])

lambda3 = np.array([
[1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
[0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
[1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
[0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0],
[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
[0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0],
[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0],
[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0],
[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0],
[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1]
])

Liste_K = [[[[[] for i in range(32)]for j in range(4)] for m in range(2)] for k in range(15)]
Liste_inconnu = []
for j in [0,2]:
    for i in range(31, -1, -1):
        if i in [27,25,14,6]:
            Liste_K[1][0][j][31-i]+=[f'K1_{j}_{i}']
    for i in range(32):
        if i in [27,25,14,6]:
            Liste_inconnu += [f'K1_{j}_{i}']
           
for i in range(31, -1, -1):
    if i not in [0, 3, 7, 8, 11, 18, 22, 23, 30]:
        Liste_K[1][1][0][31-i]+=[f'K1_4_{i}']
    if i not in [0, 3, 10 ,14, 15, 22, 24, 27, 31]:
        Liste_K[1][1][2][31-i]+=[f'K1_6_{i}']

for i in range(32):
    if i not in [0, 3, 7, 8, 11, 18, 22, 23, 30, 2, 10, 21, 29, 31]:
        Liste_inconnu += [f'K1_4_{i}']
    if i not in [0, 3, 10 ,14, 15, 22, 24, 27, 31]:
        Liste_inconnu += [f'K1_6_{i}']

for k in range(2, 15):
    if k%2==0 : #cas ou k est pair, la propagation ne mélange PAS la partie gauche avec la partie droite 
        for m in range(2):
            for j in range(32):
                #premiér block
                for element in Liste_K[k-1][m][0][(j+1)%32]:
                    if element in Liste_K[k][m][0][j]:
                        Liste_K[k][m][0][j].remove(element)
                    else :
                        Liste_K[k][m][0][j].append(element)
                for element in Liste_K[k-1][m][1][j]:
                    if element in Liste_K[k][m][0][j]:
                        Liste_K[k][m][0][j].remove(element)
                    else : 
                        Liste_K[k][m][0][j].append(element)

                #deuxieme block
                for element in Liste_K[k-1][m][2][(j+9)%32]:
                    if element in Liste_K[k][m][1][j]:
                        Liste_K[k][m][1][j].remove(element)
                    else :
                        Liste_K[k][m][1][j].append(element)
                for element in Liste_K[k-1][m][3][j]:
                    if element in Liste_K[k][m][1][j]:
                        Liste_K[k][m][1][j].remove(element)
                    else :
                         Liste_K[k][m][1][j].append(element)
                
                #troisiéme block
                for element in Liste_K[k-1][m][0][(j+1)%32]:
                    if element in Liste_K[k][m][2][j]:
                        Liste_K[k][m][2][j].remove(element)
                    else :
                        Liste_K[k][m][2][j].append(element)
                for element in Liste_K[k-1][m][1][j]:
                    if element in Liste_K[k][m][2][j]:
                        Liste_K[k][m][2][j].remove(element)
                    else : 
                        Liste_K[k][m][2][j].append(element)
                for element in Liste_K[k-1][m][1][(j+3)%32]:
                    if element in Liste_K[k][m][2][j]:
                        Liste_K[k][m][2][j].remove(element)
                    else :
                        Liste_K[k][m][2][j].append(element)   

                #Quatriéme block
                for element in Liste_K[k-1][m][2][(j+9)%32]:
                    if element in Liste_K[k][m][3][j]:
                        Liste_K[k][m][3][j].remove(element)
                    else :
                        Liste_K[k][m][3][j].append(element)
                for element in Liste_K[k-1][m][3][j]:
                    if element in Liste_K[k][m][3][j]:
                        Liste_K[k][m][3][j].remove(element)
                    else : 
                        Liste_K[k][m][3][j].append(element)
                for element in Liste_K[k-1][m][3][(j+28)%32]:
                    if element in Liste_K[k][m][3][j]:
                        Liste_K[k][m][3][j].remove(element)
                    else :
                        Liste_K[k][m][3][j].append(element)

    else : # cas ou k est impair la propagation mélange les deux parties et depend donc de m 
        for j in range(32):
            #premiér block
                for element in Liste_K[k-1][0][0][(j+1)%32]:
                    if element in Liste_K[k][0][0][j]:
                        Liste_K[k][0][0][j].remove(element)
                    else :
                        Liste_K[k][0][0][j].append(element)
                for element in Liste_K[k-1][0][1][j]:
                    if element in Liste_K[k][0][0][j]:
                        Liste_K[k][0][0][j].remove(element)
                    else : 
                        Liste_K[k][0][0][j].append(element)
            
            #deuxieme block
                for element in Liste_K[k-1][1][0][(j+1)%32]:
                    if element in Liste_K[k][0][1][j]:
                        Liste_K[k][0][1][j].remove(element)
                    else :
                        Liste_K[k][0][1][j].append(element)
                for element in Liste_K[k-1][1][1][j]:
                    if element in Liste_K[k][0][1][j]:
                        Liste_K[k][0][1][j].remove(element)
                    else : 
                        Liste_K[k][0][1][j].append(element)
            
            #troisieme block
                for element in Liste_K[k-1][0][2][(j+9)%32]:
                    if element in Liste_K[k][0][2][j]:
                        Liste_K[k][0][2][j].remove(element)
                    else :
                        Liste_K[k][0][2][j].append(element)
                for element in Liste_K[k-1][0][3][j]:
                    if element in Liste_K[k][0][2][j]:
                        Liste_K[k][0][2][j].remove(element)
                    else :
                         Liste_K[k][0][2][j].append(element)
            
            #quatrieme block
                for element in Liste_K[k-1][1][2][(j+9)%32]:
                    if element in Liste_K[k][0][3][j]:
                        Liste_K[k][0][3][j].remove(element)
                    else :
                        Liste_K[k][0][3][j].append(element)
                for element in Liste_K[k-1][1][3][j]:
                    if element in Liste_K[k][0][3][j]:
                        Liste_K[k][0][3][j].remove(element)
                    else :
                         Liste_K[k][0][3][j].append(element)

            #cinquiéme block
                for element in Liste_K[k-1][0][0][(j+1)%32]:
                    if element in Liste_K[k][1][0][j]:
                        Liste_K[k][1][0][j].remove(element)
                    else :
                        Liste_K[k][1][0][j].append(element)
                for element in Liste_K[k-1][0][1][j]:
                    if element in Liste_K[k][1][0][j]:
                        Liste_K[k][1][0][j].remove(element)
                    else : 
                        Liste_K[k][1][0][j].append(element)
                for element in Liste_K[k-1][0][1][(j+3)%32]:
                    if element in Liste_K[k][1][0][j]:
                        Liste_K[k][1][0][j].remove(element)
                    else :
                        Liste_K[k][1][0][j].append(element) 
            
            #sixiéme block
                for element in Liste_K[k-1][1][0][(j+1)%32]:
                    if element in Liste_K[k][1][1][j]:
                        Liste_K[k][1][1][j].remove(element)
                    else :
                        Liste_K[k][1][1][j].append(element)
                for element in Liste_K[k-1][1][1][j]:
                    if element in Liste_K[k][1][1][j]:
                        Liste_K[k][1][1][j].remove(element)
                    else : 
                        Liste_K[k][1][1][j].append(element)
                for element in Liste_K[k-1][1][1][(j+3)%32]:
                    if element in Liste_K[k][1][1][j]:
                        Liste_K[k][1][1][j].remove(element)
                    else :
                        Liste_K[k][1][1][j].append(element)   
            
            #septieme block
                for element in Liste_K[k-1][0][2][(j+9)%32]:
                    if element in Liste_K[k][1][2][j]:
                        Liste_K[k][1][2][j].remove(element)
                    else :
                        Liste_K[k][1][2][j].append(element)
                for element in Liste_K[k-1][0][3][j]:
                    if element in Liste_K[k][1][2][j]:
                        Liste_K[k][1][2][j].remove(element)
                    else : 
                        Liste_K[k][1][2][j].append(element)
                for element in Liste_K[k-1][0][3][(j+28)%32]:
                    if element in Liste_K[k][1][2][j]:
                        Liste_K[k][1][2][j].remove(element)
                    else :
                        Liste_K[k][1][2][j].append(element)
            
            #huitiéme block
                for element in Liste_K[k-1][1][2][(j+9)%32]:
                    if element in Liste_K[k][1][3][j]:
                        Liste_K[k][1][3][j].remove(element)
                    else :
                        Liste_K[k][1][3][j].append(element)
                for element in Liste_K[k-1][1][3][j]:
                    if element in Liste_K[k][1][3][j]:
                        Liste_K[k][1][3][j].remove(element)
                    else : 
                        Liste_K[k][1][3][j].append(element)
                for element in Liste_K[k-1][1][3][(j+28)%32]:
                    if element in Liste_K[k][1][3][j]:
                        Liste_K[k][1][3][j].remove(element)
                    else :
                        Liste_K[k][1][3][j].append(element)

print("K_3_31[0]", Liste_K[3][0][0][0])
print("K_3_31[1]", Liste_K[3][0][1][0])
print("K_3_31[2]", Liste_K[3][0][2][0])
print("K_3_31[3]", Liste_K[3][0][3][0])
print("K_3_19[0]",Liste_K[3][0][0][31-12])
print("K_3_19[1]",Liste_K[3][0][1][31-12])
print("K_3_19[2]",Liste_K[3][0][2][31-12])
print("K_3_19[3]",Liste_K[3][0][3][31-12])
print("K_3_1[0]",Liste_K[3][0][0][30])
print("K_3_1[1]",Liste_K[3][0][1][30])
print("K_3_1[2]",Liste_K[3][0][2][30])
print("K_3_1[3]",Liste_K[3][0][3][30])
"""
M13 = np.zeros((256,256), dtype=int)
M14 = np.zeros((256,256), dtype=int)    

for m in range(2):
    for i in range(4):
        for j in range(32):
            for element in Liste_K[14][m][i][j]:
                if len(element)==7:
                    M14[(4*m+i)*32+j][int(element[3])*32+int(element[5])*10+int(element[6])]=1
                elif len(element)==6:
                    M14[(4*m+i)*32+j][int(element[3])*32+int(element[5])]=1
            for element in Liste_K[13][m][i][j]:
                if len(element)==7:
                    M13[(4*m+i)*32+j][int(element[3])*32+int(element[5])*10+int(element[6])]=1
                elif len(element)==6:
                    M13[(4*m+i)*32+j][int(element[3])*32+int(element[5])]=1

M13 = M13[:,~np.all(M13 == 0, axis = 0)] #remove 0 column, variable is known
M14 = M14[:,~np.all(M14 == 0, axis = 0)]

equation_connu = [31, 28, 23, 22, 17, 14, 5, 4, 0]
L_equation_connu = []
for i in range(4):
    for element in equation_connu :
        element = 31-element
        L_equation_connu.append(i*32+element)


print(L_equation_connu)
print(M14.shape)
print(M13.shape)

#M1=np.delete(M, L_equation_inconnu, 0)
lambda0sage = [[lambda0[i][j] for j in range(lambda0.shape[1])] for i in range(lambda0.shape[0])]
lambda1sage = [[lambda1[i][j] for j in range(lambda1.shape[1])] for i in range(lambda1.shape[0])]
lambda2sage = [[lambda2[i][j] for j in range(lambda2.shape[1])] for i in range(lambda2.shape[0])]
lambda3sage = [[lambda3[i][j] for j in range(lambda3.shape[1])] for i in range(lambda3.shape[0])]
lambda0sage = Matrix(GF(2), lambda0sage)
lambda1sage = Matrix(GF(2), lambda1sage)
lambda2sage = Matrix(GF(2), lambda2sage)
lambda3sage = Matrix(GF(2), lambda3sage)
lambda0sageInv = lambda0sage.inverse()
lambda1sageInv = lambda1sage.inverse()
lambda2sageInv = lambda2sage.inverse()
lambda3sageInv = lambda3sage.inverse()

Msage0_14 = [[M14[i][j] for j in range(M14.shape[1])] for i in range(int(M14.shape[0]/2), int(M14.shape[0]/2) + int(M14.shape[0]/8))]
Msage1_14 = [[M14[i][j] for j in range(M14.shape[1])] for i in range(int(M14.shape[0]/2) + int(M14.shape[0]/8), int(M14.shape[0]/2) + int(M14.shape[0]/4))]
Msage2_14 = [[M14[i][j] for j in range(M14.shape[1])] for i in range(int(M14.shape[0]/2) + int(M14.shape[0]/4), int(M14.shape[0]/2) + int(M14.shape[0]*(3/8)))]
Msage3_14 = [[M14[i][j] for j in range(M14.shape[1])] for i in range(int(M14.shape[0]/2) + int(M14.shape[0]*(3/8)), int(M14.shape[0]/2) + int(M14.shape[0]/2))]
Msage0_14 = Matrix(GF(2), Msage0_14)
Msage1_14 = Matrix(GF(2), Msage1_14)
Msage2_14 = Matrix(GF(2), Msage2_14)
Msage3_14 = Matrix(GF(2), Msage3_14)

Msage0_14=lambda2sageInv*Msage0_14
Msage1_14=lambda2sageInv*Msage1_14
Msage2_14=lambda2sageInv*Msage2_14
Msage3_14=lambda2sageInv*Msage3_14

Usage_14 = Matrix(GF(2), Msage0_14)
Usage_14=Usage_14.stack(Msage1_14)
Usage_14=Usage_14.stack(Msage2_14)
Usage_14=Usage_14.stack(Msage3_14)

Msage0_13 = [[M13[i][j] for j in range(M13.shape[1])] for i in range(int(M13.shape[0]/8))]
Msage1_13 = [[M13[i][j] for j in range(M13.shape[1])] for i in range(int(M13.shape[0]/8), int(M13.shape[0]/4))]
Msage2_13 = [[M13[i][j] for j in range(M13.shape[1])] for i in range(int(M13.shape[0]/4), int(M13.shape[0]*(3/8)))]
Msage3_13 = [[M13[i][j] for j in range(M13.shape[1])] for i in range(int(M13.shape[0]*(3/8)), int(M13.shape[0]/2))]
Msage0_13 = Matrix(GF(2), Msage0_13)
Msage1_13 = Matrix(GF(2), Msage1_13)
Msage2_13 = Matrix(GF(2), Msage2_13)
Msage3_13 = Matrix(GF(2), Msage3_13)

Msage0_13=lambda1sageInv*Msage0_13
Msage1_13=lambda1sageInv*Msage1_13
Msage2_13=lambda1sageInv*Msage2_13
Msage3_13=lambda1sageInv*Msage3_13

Usage_13 = Matrix(GF(2), Msage0_13)
Usage_13=Usage_13.stack(Msage1_13)
Usage_13=Usage_13.stack(Msage2_13)
Usage_13=Usage_13.stack(Msage3_13)

Usage14_36_known_equation = Usage_14.matrix_from_rows(L_equation_connu)

Usage_14_36_echelon = Usage14_36_known_equation.echelon_form()

Liste_indice_equations = []
for i in range(Usage_14_36_echelon.ncols()):
    compteur = 0
    for j in range(Usage_14_36_echelon.nrows()):
        compteur += int(Usage_14_36_echelon[j][i]) 
    if compteur >=2 :
        Liste_indice_equations.append(i)

state_test_equation_variables = [[] for i in range(36)]

for j in range(4):
    for i in Liste_indice_equations:
        state_test_equation_variables[j*9].append(Usage_13[32*j+31-28][i])
        state_test_equation_variables[j*9+1].append(Usage_13[32*j+31-23][i])
        state_test_equation_variables[j*9+2].append(Usage_13[32*j+31-4][i])
        state_test_equation_variables[j*9+3].append(Usage_14[32*j+31-29][i])
        state_test_equation_variables[j*9+4].append(Usage_14[32*j+31-27][i])
        state_test_equation_variables[j*9+5].append(Usage_14[32*j+31-18][i])
        state_test_equation_variables[j*9+6].append(Usage_14[32*j+31-12][i])
        state_test_equation_variables[j*9+7].append(Usage_14[32*j+31-10][i])
        state_test_equation_variables[j*9+8].append(Usage_14[32*j+31-1][i])

    print(f'U13_28_{j} :', state_test_equation_variables[j*9])
    print(f'U13_23_{j} :', state_test_equation_variables[j*9+1])
    print(f'U13_4_{j}  :', state_test_equation_variables[j*9+2])
    print(f'U14_29_{j} :', state_test_equation_variables[j*9+3])
    print(f'U14_27_{j} :', state_test_equation_variables[j*9+4])
    print(f'U14_18_{j} :', state_test_equation_variables[j*9+5])
    print(f'U14_12_{j} :', state_test_equation_variables[j*9+6])
    print(f'U14_10_{j} :', state_test_equation_variables[j*9+7])
    print(f'U14_1_{j}  :', state_test_equation_variables[j*9+8])
    
state_test_equation_variables = Matrix(GF(2), state_test_equation_variables)

U13_28 = state_test_equation_variables.matrix_from_rows([0, 9, 18, 27])
U13_23 = state_test_equation_variables.matrix_from_rows([1, 10, 19, 28])
U13_4 = state_test_equation_variables.matrix_from_rows([2, 11, 20, 29])

U14_29 = state_test_equation_variables.matrix_from_rows([3, 12, 21, 30])
U14_27 = state_test_equation_variables.matrix_from_rows([4, 13, 22, 31])
U14_18 = state_test_equation_variables.matrix_from_rows([5, 14, 23, 32])
U14_12 = state_test_equation_variables.matrix_from_rows([6, 15, 24, 33])
U14_10 = state_test_equation_variables.matrix_from_rows([7, 16, 25, 34])
U14_1 = state_test_equation_variables.matrix_from_rows([8, 17, 26, 35])

print("")
print("13_28 et 14_1  : rank=", (U13_28.stack(U14_1)).rank())
print("13_28 et 14_18 : rank=", (U13_28.stack(U14_18)).rank())
print("14_1 et 14_18  : rank=", (U14_1.stack(U14_18)).rank())
print("13_28 et 14_1 et 14_18 : rank=",(U13_28.stack(U14_1.stack(U14_18))).rank())
print("")

print("13_23 et 14_2  : rank=", (U13_23.stack(U14_12)).rank())
print("13_23 et 14_29 : rank=", (U13_23.stack(U14_29)).rank())
print("14_12 et 14_29 : rank=", (U14_12.stack(U14_29)).rank())
print("13_23 et 14_2 et 14_29 : rank=", (U13_23.stack(U14_12.stack(U14_29))).rank())
print("")

print("13_4 et 14_10  : rank=", (U13_4.stack(U14_10)).rank())
print("13_4 et 14_27  : rank=", (U13_4.stack(U14_27)).rank())
print("14_10 et 14_27 : rank=", (U14_10.stack(U14_27)).rank())
print("13_4 et 14_10 et 14_27 : rank=", (U13_4.stack(U14_10.stack(U14_27))).rank())
print("")

print("Up with 13_23 et 14_12 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U13_23.stack(U14_12))))).rank())
print("Up with 13_23 et 14_29 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U13_23.stack(U14_29))))).rank())
print("Up with 14_12 et 14_29 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U14_12.stack(U14_29))))).rank())
print("")
print("Up with 13_4 et 14_10 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U13_4.stack(U14_10))))).rank())
print("Up with 13_4 et 14_27 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U13_4.stack(U14_27))))).rank())
print("Up with 14_10 et 14_27 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U14_10.stack(U14_27))))).rank())
print("")
print("")
print("Up with 13_4 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U13_4)))).rank())
print("Up with 14_27 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U14_27)))).rank())
print("Up with 14_10 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U14_10)))).rank())
print("")
print("Up with 13_23 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U13_23)))).rank())
print("Up with 14_12 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U14_12)))).rank())
print("Up with 14_29 : rank=", (U13_28.stack(U14_1.stack(U14_18.stack(U14_29)))).rank())
print("")
print("13_28 et 14_1 echelonize :")
print((U13_28.stack(U14_1)).echelon_form())
print("")
print("13_28 et 14_18 echelonize :")
print((U13_28.stack(U14_18)).echelon_form())
print("")
print("14_1 et 14_18 echelonize :")
print((U14_1.stack(U14_18)).echelon_form())
print("")
print("13_23 et 14_12 echelonize :")
print((U13_23.stack(U14_12)).echelon_form())
print("")
print("13_23 et 14_29 echelonize :")
print((U13_23.stack(U14_29)).echelon_form())
print("")
print("14_12 et 14_29 echelonize :")
print((U14_12.stack(U14_29)).echelon_form())
print("")
print("13_4 et 14_10 echelonize :")
print((U13_4.stack(U14_10)).echelon_form())
print("")
print("13_1 et 14_27 echelonize :")
print((U13_4.stack(U14_27)).echelon_form())
print("")
print("14_10 et 14_27 echelonize :")
print((U14_10.stack(U14_27)).echelon_form())
print("")
"""