#!/usr/bin/env python3
import sys

import matplotlib.pyplot as plt

from main import read_coords_from_txt


if __name__ == '__main__':
    panel = read_coords_from_txt(sys.argv[1], delimiter=',')

    plt.rcParams['figure.figsize'] = (12, 12)
    plt.gca().set_aspect('equal')
    plt.scatter(panel[:, 0], panel[:, 1])
    plt.show()
