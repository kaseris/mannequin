import json

import numpy as np
from matplotlib.path import Path as MPLPath
from matplotlib.patches import PathPatch as MPLPathPatch


class Accessory:

    __JSON_TO_PATH = {'lineto': MPLPath.LINETO,
                      'moveto': MPLPath.MOVETO,
                      'curve3': MPLPath.CURVE3,
                      'curve4': MPLPath.CURVE4,
                      'closepoly': MPLPath.CLOSEPOLY}
    MARGIN = 2

    def __init__(self, pocket_type):
        self.__interactive_line = None
        self.__center = np.array([[0.0, 0.0]])
        self.__points = []
        self.__scale = 1.0
        self.pocket_type = pocket_type
        self.__path_data = []
        self.scale_factor = 1.0
        self.__initial_points = None
        self.__built = False
        self.__path = None
        self.__patch = None

    def edit(self):
        pass

    def build(self):
        # TODO: Upon creation, also build a PathPatch object given the codes and the verts, instead of creating it in
        # TODO: the WindowAccessoryEditor.
        with open('pockets.json', 'r') as f:
            pocket_data = json.load(f)

        instructions = pocket_data[self.pocket_type]
        for instruction, point in instructions:
            self.__path_data.append((Accessory.__JSON_TO_PATH[instruction], tuple(point)))
            self.__points.append(point)
        # We append an extra vertex to the centre of mass of the polygon. This will serve as a polygon translate
        # anchor.
        codes, verts = zip(*self.__path_data)
        self.__path = MPLPath(verts, codes)
        # Leave it as is for now
        self.__patch = MPLPathPatch(self.__path, facecolor='green', edgecolor='red', alpha=1.0, zorder=0)
        self.__patch.set_animated(False)
        self.__path_data.append((Accessory.__JSON_TO_PATH['moveto'], np.mean(self.points[:-1], axis=0).tolist()))
        self.__points.append(np.mean(self.points[:-1], axis=0).tolist())
        if not self.__built:
            self.__initial_points = self.__points.copy()
            self.__built = True

    def update(self, pocket_type):
        self.__path_data = []
        self.__points = []
        self.pocket_type = pocket_type
        self.__built = False
        self.build()
        self.scale(self.scale_factor)

    def translate(self, dx, dy):
        tmp = []
        for idx, point in enumerate(self.__points):
            # Update the internal point data
            tmp.append([point[0] + dx, point[1] + dy])
        # Update the path data
        self.__points = tmp
        self.update_path_data()

    def scale(self, scale):
        self.scale_factor = scale
        for idx, point in enumerate(self.__initial_points):
            # Update the internal point data
            self.__points[idx] = [point[0] * self.scale_factor, point[1] * self.scale_factor]
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
        left = np.min(_points[:, 0] - Accessory.MARGIN)
        right = np.max(_points[:, 0] + Accessory.MARGIN)
        return left, right

    @property
    def ylim(self):
        _points = np.asarray(self.__points)
        down = np.min(_points[:, 1] - Accessory.MARGIN)
        up = np.max(_points[:, 1] + Accessory.MARGIN)
        return down, up

    @property
    def available_accessories(self):
        with open('pockets.json', 'r') as f:
            data = json.load(f)
        return list(data.keys())

    @property
    def path_(self):
        return self.__path

    @property
    def pathpatch(self):
        return self.__patch


if __name__ == '__main__':
    pocket = Accessory('triangle_pocket')
    pocket.build()
    print(f'points:\n{pocket.points}')
    pocket.update('square_pocket')
    import matplotlib.pyplot as plt
    from image_view import PathInteractor
    from matplotlib.patches import PathPatch

    fig, ax = plt.subplots()
    codes, verts = zip(*pocket.path_data)
    path = MPLPath(verts, codes)
    patch = MPLPathPatch(
        path, facecolor=None, edgecolor='black', alpha=1.0, fill=True)
    ax.add_patch(patch)

    interactor = PathInteractor(patch)
    ax.set_title('drag vertices to update path')
    ax.set_xlim(pocket.xlim)
    ax.set_ylim(pocket.ylim)

    plt.show()
