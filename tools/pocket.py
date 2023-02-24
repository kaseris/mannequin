import json

import numpy as np
from matplotlib.path import Path


class Pocket:

    __JSON_TO_PATH = {'lineto': Path.LINETO,
                      'moveto': Path.MOVETO,
                      'curve3': Path.CURVE3,
                      'curve4': Path.CURVE4,
                      'closepoly': Path.CLOSEPOLY}
    MARGIN = 2

    def __init__(self, pocket_type):
        self.__interactive_line = None
        self.__center = np.array([[0.0, 0.0]])
        self.__points = []
        self.__scale = 1.0
        self.pocket_type = pocket_type
        self.__path_data = []

    def edit(self):
        pass

    def build(self):
        with open('pockets.json', 'r') as f:
            pocket_data = json.load(f)

        instructions = pocket_data[self.pocket_type]
        for instruction, point in instructions:
            self.__path_data.append((Pocket.__JSON_TO_PATH[instruction], point))
            self.__points.append(point)
        # We append an extra vertex to the centre of mass of the polygon. This will serve as a polygon translate
        # anchor.
        self.__path_data.append((Pocket.__JSON_TO_PATH['moveto'], np.mean(self.points[:-1], axis=0).tolist()))
        self.__points.append(np.mean(self.points, axis=0).tolist())

    def update(self):
        pass

    def translate(self, dx, dy):
        for idx, point in enumerate(self.__points):
            # Update the internal point data
            self.__points[idx] = [point[0] + dx, point[1] + dy]
        # Update the path data
        self.update_path_data()

    def scale(self, scale):
        for idx, point in enumerate(self.__points):
            # Update the internal point data
            self.__points[idx] = [point[0] * scale, point[1] * scale]
        # Update the path data
        self.update_path_data()

    def update_path_data(self):
        tmp = []
        for point in self.__points:
            tmp.append(point)

        new_path_data = []
        for new_point, tup in zip(tmp, self.__path_data):
            instruction, point = tup
            new_path_data.append((instruction, new_point))
        self.__path_data = new_path_data

    def remove(self):
        pass

    @property
    def interactive_line(self):
        return self.__interactive_line

    @property
    def path_data(self):
        return self.__path_data

    @property
    def points(self):
        return np.asarray(self.__points)

    @property
    def xlim(self):
        _points = np.asarray(self.__points)
        left = np.min(_points[:, 0] - Pocket.MARGIN)
        right = np.max(_points[:, 0] + Pocket.MARGIN)
        return left, right

    @property
    def ylim(self):
        _points = np.asarray(self.__points)
        down = np.min(_points[:, 1] - Pocket.MARGIN)
        up = np.max(_points[:, 1] + Pocket.MARGIN)
        return down, up


if __name__ == '__main__':
    pocket = Pocket('triangle_pocket')
    pocket.build()
    print(f'points:\n{pocket.points}')
    import matplotlib.pyplot as plt
    from image_view import PathInteractor
    from matplotlib.patches import PathPatch

    fig, ax = plt.subplots()
    codes, verts = zip(*pocket.path_data)
    path = Path(verts, codes)
    patch = PathPatch(
        path, facecolor=None, edgecolor='black', alpha=1.0, fill=True)
    ax.add_patch(patch)

    interactor = PathInteractor(patch)
    ax.set_title('drag vertices to update path')
    ax.set_xlim(pocket.xlim)
    ax.set_ylim(pocket.ylim)

    plt.show()
