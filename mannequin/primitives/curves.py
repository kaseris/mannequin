import numpy as np
from scipy.special import comb


class Line:
    def __init__(self, *cps):
        assert len(cps) == 2

        self.x1 = cps[0][0]
        self.y1 = cps[0][1]
        self.x2 = cps[1][0]
        self.y2 = cps[1][1]

    def __str__(self):
        s = f'----- Line -----\n'
        s += f'\t\tStarting point: ({self.x1, self.y1})\n'
        s += f'\t\tEnding point: ({self.x2, self.y2})'
        return s

    @property
    def curve(self):
        return np.array([[self.x1, self.y1],
                         [self.x2, self.y2]])

    @property
    def start(self):
        return (self.x1, self.y1)

    @property
    def end(self):
        return (self.x2, self.y2)

    @property
    def length(self):
        y_sq = np.power(self.y2 - self.y1, 2)
        x_sq = np.power(self.x2 - self.x1, 2)
        return np.sqrt(y_sq + x_sq)


class BezierCurve:
    def __init__(self, *cps):

        # for arg in cps:
        #     if not (isinstance(arg, tuple) or isinstance(arg, list)):
        #         raise ValueError('`arg` must be one of the following: `tuple`, `list`.')

        self.__n_cps = len(cps)

        self.resolution = 10
        self.t = np.linspace(0.0, 1.0, self.resolution)

        for idx, point in enumerate(cps):
            setattr(self, 'cp' + str(idx + 1), point)

        self.__points = self.__make_curve()

    def __str__(self):
        s = f'----- Bézier Curve with {self.n_cps} control points -----\n'
        for i in range(self.n_cps):
            s += f'\t\tControl point {i + 1}: {getattr(self, "cp" + str(i + 1))}\n'
        return s

    def _bernstein_polynomial(self, i, n, t):
        return comb(n, i) * ((1 - t) ** (n - i)) * t ** i

    def __make_curve(self):
        control_point_X = np.array([getattr(self, 'cp' + str(i + 1))[0] for i in range(self.__n_cps)])
        control_point_Y = np.array([getattr(self, 'cp' + str(i + 1))[1] for i in range(self.__n_cps)])

        bezier_coefficients = np.array(
            [self._bernstein_polynomial(i, self.__n_cps - 1, self.t) for i in range(self.__n_cps)])
        xx, yy = np.dot(control_point_X, bezier_coefficients), np.dot(control_point_Y, bezier_coefficients)
        return np.column_stack((xx, yy))

    @property
    def curve(self):
        return self.__points

    @property
    def control_points(self):
        control_points = []
        for i in range(self.n_cps):
            control_points.append(getattr(self, 'cp' + str(i + 1)))
        return control_points

    @property
    def n_cps(self):
        return self.__n_cps

    @property
    def start(self):
        return self.cp1

    @property
    def end(self):
        return getattr(self, 'cp' + str(len(self.__n_cps)))


class Edge:
    EDGE_TYPES = {
        'line': Line,
        'bez': BezierCurve,
        'bezier': BezierCurve
    }

    def __init__(self, **props):
        self.kind = props['type']
        self.curve_object = self.EDGE_TYPES[self.kind](*props['control_points'])

    @property
    def start_point(self):
        return self.curve_object.start

    @property
    def end_point(self):
        return self.curve_object.end

    @property
    def curve_points(self):
        return self.curve_object.curve

    def __repr__(self):
        return str(self.curve_object)
