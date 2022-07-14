from mannequin.primitives.curves import *


class Panel:

    def __init__(self, **props):
        self.__name = props['name']
        self.__edges = dict()
        self.__points = []

        edge_names = list(props.keys())[1:]
        for edge_name in edge_names:
            self.__edges[edge_name] = Edge(**props[edge_name])
            self.__points.append(self.__edges[edge_name].curve_points)

    def __str__(self):
        s = f'---- PANEL -----\n'
        s += f'Panel name: {self.__name}\n'
        for k, v in self.__edges.items():
            s += f'\tEdge: ({k})\n'
            s += f'\tCurve type: \n'
            s += f'\t\t{str(v)}\n'
        return s

    def __getitem__(self, edge_name):
        return self.__edges[edge_name]

    @property
    def name(self):
        return self.__name

    @property
    def edges(self):
        return self.__edges

    @property
    def point_cloud(self):
        return np.vstack(self.__points)
