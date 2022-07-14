import numpy as np
from scipy.special import comb


def bernstein_poly(i, n, t):
    return comb(n, i) * ( t**(n-i) ) * (1 - t)**i


def bezier_curve(points, nTimes=1000):
    nPoints = len(points)
    xPoints = np.array([p[0] for p in points])
    yPoints = np.array([p[1] for p in points])

    t = np.linspace(0.0, 1.0, nTimes)

    polynomial_array = np.array([bernstein_poly(i, nPoints - 1, t) for i in range(0, nPoints)])

    xvals = np.dot(xPoints, polynomial_array)
    yvals = np.dot(yPoints, polynomial_array)

    return xvals, yvals


def fit_bezier(points_of_curve, deg):
    tData = np.linspace(0, 1, points_of_curve.shape[0])

    Mtk = lambda n, t, k: t ** k * (1 - t) ** (n - k) * comb(n, k)
    bezier_coeff = lambda ts: [[Mtk(deg, t, k) for k in range(deg + 1)] for t in ts]

    pinv = np.linalg.pinv(bezier_coeff(tData))
    control_points = pinv.dot(points_of_curve)
    return control_points
