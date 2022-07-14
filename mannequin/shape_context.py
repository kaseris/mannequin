import heapq
import math
import sys
import time

import numpy as np
import scipy.optimize
from scipy.interpolate import Rbf, InterpolatedUnivariateSpline, interp1d
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment

import munkres
from utils import bookstein


def logspace(d1, d2, n):
    sp = [(10 ** (d1 + k * (d2 - d1) / (n - 1))) for k in range(0, n - 1)]
    sp.append(10 ** d2)
    return sp


def euclidean_distance(p1, p2):
    return np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def get_angle(p1, p2):
    """Returns the angle in rads."""
    return np.arctan2((p2[1] - p1[1]), (p2[0] - p1[0]))


class ShapeContext:
    HUNGARIAN = 1
    # good values: 1e-10, 1e+10

    def __init__(self,
                 n_bins_r=1,
                 n_bins_theta=1,
                 r_inner=0.01,
                 r_outer=1e+5):
        self.n_bins_r = n_bins_r
        self.n_bins_theta = n_bins_theta
        self.r_inner = r_inner
        self.r_outer = r_outer
        self.n_bins = n_bins_r * n_bins_theta

    def _dist2(self, x, c):
        result = np.zeros((len(x), len(c)))
        for i in range(len(x)):
            for j in range(len(c)):
                result[i, j] = euclidean_distance(x[i], c[j])
        return result

    def _get_angles(self, x):
        result = np.zeros((len(x), len(x)))
        for i in range(len(x)):
            for j in range(len(x)):
                result[i, j] = get_angle(x[i], x[j])
        return result

    def get_mean(self, matrix):
        return np.mean(matrix)

    def compute(self, points, r=None):
        t = time.time()
        r_array = cdist(points, points)
        mean_dist = r_array.mean()
        r_array_n = r_array / mean_dist

        r_bin_edges = logspace(np.log10(self.r_inner),
                               np.log10(self.r_outer),
                               self.n_bins_r)

        r_array_q = np.zeros((len(points), len(points)), dtype=int)
        for m in range(self.n_bins_r):
            r_array_q += (np.log10(r_array_n) < r_bin_edges[m])

        fz = r_array_q > 0

        theta_array = self._get_angles(points)
        # Shift by 2*pi
        theta_array_2 = theta_array + 2 * np.pi * (theta_array < 0)
        theta_array_q = 1 + np.floor(theta_array_2 / (2 * np.pi / self.n_bins_theta))
        theta_array_q = theta_array_q.astype('int')

        BH = np.zeros((len(points), self.n_bins))
        for i in range(len(points)):
            sn = np.zeros((self.n_bins_r, self.n_bins_theta))
            for j in range(len(points)):
                if fz[i, j]:
                    sn[r_array_q[i, j] - 1, theta_array_q[i, j] - 2] += 1
            BH[i] = sn.reshape(self.n_bins)

        print(f'Profile Total Cost: {str(time.time() - t)}')

        return BH

    def _cost(self, hi, hj):
        cost = 0
        for k in range(self.n_bins):
            if hi[k] + hj[k]:
                cost += ((hi[k] - hj[k]) ** 2) / (hi[k] + hj[k])
        return cost * 0.5

    def cost(self, P, Q, qlength=None):
        p = P.shape[0]
        p2 = Q.shape[0]
        d = p2
        if qlength:
            d = qlength
        C = np.zeros((p, p2))
        for i in range(p):
            for j in range(p2):
                C[i, j] = self._cost(Q[j] / d, P[i] / p)
        return C

    def __hungarian_method(self, cost_matrix):
        # print(f'Inside: {__name__}')
        st = time.time()
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        total = cost_matrix[row_ind, col_ind].sum()
        # print(total)
        indexes = [[p, q] for p, q in zip(row_ind, col_ind)]
        # print(f'indexes: {list(indexes)}')
        print(f'Profile Hungarian: {time.time() - st}')
        return total, indexes
        '''
        t = time.time()
        m = munkres.Munkres()
        indexes = m.compute(C.tolist())
        total = 0
        for row, column in indexes:
            value = C[row][column]
            total += value
        print(f'Profile Hungarian Algorithm: {str(time.time() - t)}')
        return total, indexes
        '''

    def quick_diff(self,
                   P: np.ndarray,
                   Qs: np.ndarray,
                   method=HUNGARIAN):
        res = []

        p = P.shape[0]
        q = Qs.shape[0]
        for i in range(p):
            for j in range(q):
                heapq.heappush(res, (self._cost(P[i], Qs[j]), i))

        data = np.zeros((q, self.n_bins))
        for i in range(q):
            data[i] = P[heapq.heappop(res)[1]]

        return self.diff(data, Qs)

    def diff(self, P, Q, qlength=None, method=HUNGARIAN):
        """
                    if Q is generalized shape context then it compute shape match.
                    if Q is r point representative shape contexts and qlength set to
                    the number of points in Q then it compute fast shape match.
        """
        # result = None
        C = self.cost(P, Q, qlength)

        if method == self.HUNGARIAN:
            result = self.__hungarian_method(C)
        else:
            raise Exception('No such optimisation method')

        return result

    def get_contexts(self, BH, r=5):
        res = np.zeros((r, self.n_bins))
        used = []
        sums = []

        for i in range(len(BH)):
            heapq.heappush(sums, (np.sum(BH[i]), i))

        for i in range(r):
            _, l = heapq.heappop(sums)
            res[i] = BH[l]
            used.append(l)

        del sums

        return res, used

    def interpolate(self, P1, P2):
        t = time.time()
        assert len(P1) == len(P2), 'Shapes do not have equal number of points'
        x = [0] * len(P1)
        xs = [0] * len(P1)
        y = [0] * len(P1)
        ys = [0] * len(P1)
        for i in range(len(P1)):
            x[i] = P1[i][0]
            xs[i] = P2[i][0]
            y[i] = P1[i][1]
            ys[i] = P2[i][1]

        def U(r):
            res = r ** 2 * np.log10(r ** 2)
            res[r == 0] = 0
            return res

        SM = .15
        fx = Rbf(x, xs, function=U, smooth=SM)
        fy = Rbf(y, ys, function=U, smooth=SM)

        cx, cy, E, affcost, L = bookstein(P1, P2, 15)

        print(f'Profile TPS Interpolation: {str(time.time() - t)}')

        return fx, fy, E, float(affcost)
