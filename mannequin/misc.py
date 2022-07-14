import matplotlib.pyplot as plt
import numpy as np


def plot_matching_with_annos(pc1, pc2, lines_cor, lines_inc):
    plt.rcParams['figure.figsize'] = (12, 12)
    plt.gca().set_aspect('equal')
    plt.scatter(pc1[:, 0], pc1[:, 1])
    plt.scatter(pc2[:, 0], pc2[:, 1])

    for line in lines_cor:
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), 'g--')

    for line in lines_inc:
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), 'r--')

    plt.legend(['reference', 'input'])
    plt.show()


def plot_matching(pc1, pc2, lines):
    plt.rcParams['figure.figsize'] = (12, 12)
    plt.gca().set_aspect('equal')
    plt.scatter(pc1[:, 0], pc1[:, 1])
    plt.scatter(pc2[:, 0], pc2[:, 1])

    for line in lines:
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), 'k--')
    plt.legend(['reference', 'input'])
    plt.show()


def normalize(_src):
    src_min_x = np.min(_src[:, 0])
    src_min_y = np.min(_src[:, 1])

    _src[:, 0] -= src_min_x
    _src[:, 1] -= src_min_y

    src_max_x = np.max(_src[:, 0])
    src_max_y = np.max(_src[:, 1])

    _src[:, 0] /= src_max_x
    _src[:, 1] /= src_max_y
    return _src
