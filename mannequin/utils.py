import heapq as hq
import math
import sys
import time
import urllib

import numpy as np
import scipy
from scipy.spatial.distance import euclidean, cdist


def euclidean_distance(p1, p2):
    return np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def dist2(x, c):
    ncentres = c.shape[0]
    ndata = x.shape[0]
    return (np.ones((ncentres, 1)) * (np.power(x, 2)).H.sum(axis=0)) + np.ones((ndata, 1)) \
           * (np.power(c, 2)).H.sum(axis=0) - np.multiply(2, (x * c.H))


def bookstein(X, Y, beta):
    X = np.asmatrix(X)
    Y = np.asmatrix(Y)

    N = X.shape[0]
    r2 = cdist(X, X)
    K = np.multiply(r2, np.log10(r2 + np.eye(N, N)))
    P = np.concatenate((np.ones((N, 1)), X), 1)
    L = np.bmat([[K, P], [P.H, np.zeros((3, 3))]])
    V = np.concatenate((Y.H, np.zeros((2, 3))), 1)

    L[0:N, 0:N] = L[0:N, 0:N] + beta * np.eye(N, N)

    # L = L[np.logical_not(np.isnan(L))]
    print(f'L.shape: {L.shape}')
    invL = scipy.linalg.inv(L)

    c = invL * V.H
    cx = c[:, 0]
    cy = c[:, 1]

    Q = c[0:N, :].H * K * c[0:N, :]
    E = np.mean(np.diag(Q))

    n_good = 10

    A = np.concatenate((cx[n_good+2:n_good+3, :], cy[n_good+2:n_good+3, :]), 1)
    s = np.linalg.svd(A)
    aff_cost = np.log10(s[0] / s[1])

    return cx, cy, E, aff_cost, L


def gauss_kernel(N):
    g = 2**(1-N)*np.diag(np.fliplr(pascal(N)))
    W = g * g.H


def pascal(n, k=0):
    p = np.diag((-1)**np.arange(n))
    p[:, 0] = np.ones(n)

    # Generate the Pascal Cholesky factor
    for j in range(1, n-1):
        for i in range(j+1, n):
            p[i, j] = p[i-1, j] - p[i-1, j-1]

    if k == 0:
        p = np.matrix(p) * np.matrix(p.T)
    elif k == 2:
        p = np.rot90(p, 3)
        if n / 2 == np.round(n/2):
            p = -p

    return p


def get_symmetric_part(panel: np.ndarray) -> np.ndarray:
    """Given a panel's point cloud, returns the right hand side symmetric part of the panel.

    :param panel:
    :return: The sliced array where its points lie on the right of the vertical symmetry axis
    """
    # Parameter check
    if not isinstance(panel, np.ndarray):
        raise TypeError('Argument `panel` must be of type `np.ndarray`.')

    if not panel.shape[1] == 2:
        raise ValueError('`panel` must be a Nx2 array.')

    # Find the point in x where the axis of symmetry crosses.
    min_x = np.min(panel[:, 0])
    max_x = np.max(panel[:, 0])
    symmetry_x = min_x + ((max_x - min_x) / 2.0)
    # Return the sliced array where its points lie on the right of the vertical symmetry axis
    return panel[panel[:, 0] <= symmetry_x]


if __name__ == '__main__':
    a = np.random.randn(15, 2)
    b = np.random.randn(5, 2)
    res = dist2(a, b)
    print(f'res: {res}')
    print(f'res.shape: {res.shape}')