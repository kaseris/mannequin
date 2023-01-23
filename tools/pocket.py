import json

import numpy as np
from matplotlib.path import Path


class Pocket:

    __JSON_TO_PATH = {'lineto': Path.LINETO,
                      'moveto': Path.MOVETO,
                      'closepoly': Path.CLOSEPOLY}

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

    def update(self):
        pass

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
        path, facecolor=None, edgecolor='black', alpha=1.0, fill=False)
    ax.add_patch(patch)

    interactor = PathInteractor(patch)
    ax.set_title('drag vertices to update path')
    ax.set_xlim(-3, 4)
    ax.set_ylim(-3, 4)

    plt.show()
