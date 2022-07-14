import sys

import matplotlib.pyplot as plt
import numpy as np
import scipy.spatial.distance as distance

from shape_context import ShapeContext
from TPS import TPS_generate, TPS_grid, TPS_project


def save_txt(fname, obj):
    with open(fname, 'w') as f:
        for point in obj:
            x, y = point
            f.write(f'{str(x)},{str(y)}\n')


def plot_matching(pc1, pc2, lines):
    plt.rcParams['figure.figsize'] = (12, 12)
    plt.gca().set_aspect('equal')
    plt.scatter(pc1[:, 0], pc1[:, 1])
    plt.scatter(pc2[:, 0], pc2[:, 1])

    for line in lines:
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), 'k--')
    plt.legend(['reference', 'input'])
    plt.show()

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

def read_coords_from_txt(path, delimiter=' '):
    coords = []
    with open(path, 'r') as f:
        for idx, line in enumerate(f):
            line = line.split(delimiter)
            x, y = float(line[0]), float(line[-1])
            coords.append([x, y])
    return np.asarray(coords)


def sort_xy(x, y):
    x0 = np.mean(x)
    y0 = np.mean(y)

    r = np.sqrt((x - x0) ** 2 + (y - y0) ** 2)

    angles = np.where((y - y0) > 0, np.arccos((x - x0) / r), 2 * np.pi - np.arccos((x - x0) / r))

    mask = np.argsort(angles)

    x_sorted = x[mask]
    y_sorted = y[mask]

    return np.column_stack((x_sorted, y_sorted))


def rotate(coords, angle=30):
    angle_rad = np.deg2rad(angle)
    R = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                  [np.sin(angle_rad), np.cos(angle_rad)]])

    return np.dot(coords, R.T)


def enlarge_contour(c1, point_count):
    """
    Returns a contour that has point_count points.
    :param c1: A contour that has at most point_count points. If c1 has
        the same number or more of points as point_count, returns c1.
    :param point_count:
    :returns: A new contour that has all points from c1 and new
        points obtained by linear interpolation between the points
        with the biggest distance.
    """
    to_add = point_count - c1.shape[0]
    if to_add <= 0:
        return c1
    c1 = c1.reshape((c1.shape[0], c1.shape[-1]))
    dists = []
    for (idx, i) in enumerate(c1[1:]):
        dists.append((distance.euclidean(c1[idx], i), idx))
    dists.sort(reverse=1)
    # interpolate between c1[i0], c1[i0+1]
    add_idxs = []
    add_items = []
    for i in range(max(1, min(len(dists)//2, to_add))):
        i0 = dists[i][1]
        new_pt = c1[i0] + (c1[i0+1] - c1[i0])/2
        add_idxs.append(i0+1)
        add_items.append(new_pt)
    c1 = np.insert(c1, add_idxs, add_items, 0)
    return enlarge_contour(c1, point_count)


if __name__ == '__main__':
    ref = sys.argv[1]
    target = sys.argv[2]

    try:
        ENLARGE_CONTOUR_TO_N = int(sys.argv[3])
        SUBSAMPLED_SHAPE_N = int(sys.argv[4])
    except IndexError:
        ENLARGE_CONTOUR_TO_N = 20000
        SUBSAMPLED_SHAPE_N = 128

    STEP = 2

    coords = read_coords_from_txt(ref, delimiter=',')
    coords_target = read_coords_from_txt(target, delimiter=',')
    # coords_target -= 400.0

    # coords = sort_xy(coords[:, 0], coords[:, 1])
    # coords_target = sort_xy(coords_target[:, 0], coords_target[:, 1])

    # coords = np.vstack((coords, coords[0]))
    # coords_target = np.vstack((coords_target, coords_target[0]))
    # #
    # coords = enlarge_contour(coords, ENLARGE_CONTOUR_TO_N)
    # coords_target = enlarge_contour(coords_target, ENLARGE_CONTOUR_TO_N)
    #
    # idx_src = np.random.permutation(np.arange(coords.shape[0]))
    # idx_dst = np.random.permutation(np.arange(coords_target.shape[0]))
    #
    # # coords = coords[idx_src]
    # # coords_target = coords_target[idx_src]
    #
    coords = coords[::STEP]
    coords_target = coords_target[::STEP]

    # coords_target += 400.0
    sc = ShapeContext()

    P = sc.compute(coords)
    Q = sc.compute(coords_target)

    cost, indices = sc.diff(P=P, Q=Q)

    pp = []
    qp = []
    for i, k in indices:
        qp.append(coords_target[i])
        pp.append(coords[k])

    # save_txt('qp.txt', qp)
    # save_txt('pp.txt', pp)

    # fx, fy, diff, affcost = sc.interpolate(qp, pp)
    lines = []
    lines_correct = []
    lines_incorrect = []
    matches = dict()
    matches['src'] = []
    matches['matches'] = []
    for p1, q1 in indices:
        # print(f'p1: {p1}')
        # print(f'q1: {q1}')
        if p1 == q1:
            lines_correct.append([[coords[p1][0], coords[p1][1]], [coords_target[q1][0], coords_target[q1][1]]])
        else:
            lines_incorrect.append([[coords[p1][0], coords[p1][1]], [coords_target[q1][0], coords_target[q1][1]]])

        matches['src'].append(coords[p1])
        matches['matches'].append(coords_target[q1])
        lines.append([[coords[p1][0], coords[p1][1]], [coords_target[q1][0], coords_target[q1][1]]])

    save_txt('src.txt', matches['src'])
    save_txt('matches.txt', matches['matches'])
    plot_matching(coords, coords_target, lines)
    plot_matching_with_annos(coords, coords_target, lines_correct, lines_incorrect)

    src = [x.tolist() for x in matches['src']]
    dst = [x.tolist() for x in matches['matches']]
    # src = matches['src'].tolist()
    # dst = matches['matches'].tolist()

    # g = TPS_generate(src, dst)

    # print(f'Bending energy: {g["be"]:.3f}')

    _src = np.asarray(matches['src'])
    _dst = np.asarray(matches['matches'])

    src_min_x = np.min(_src[:, 0])
    src_min_y = np.min(_src[:, 1])

    _src[:, 0] -= src_min_x
    _src[:, 1] -= src_min_y

    src_max_x = np.max(_src[:, 0])
    src_max_y = np.max(_src[:, 1])

    _src[:, 0] /= src_max_x
    _src[:, 1] /= src_max_y

    ##
    dst_min_x = np.min(_dst[:, 0])
    dst_min_y = np.min(_dst[:, 1])

    _dst[:, 0] -= dst_min_x
    _dst[:, 1] -= dst_min_y

    dst_max_x = np.max(_dst[:, 0])
    dst_max_y = np.max(_dst[:, 1])

    _dst[:, 0] /= dst_max_x
    _dst[:, 1] /= dst_max_y

    g2 = TPS_generate(_src, _dst)
    print(f'Bending energy: {g2["be"]:.3f}')

    grid = TPS_grid(
        g=g2,
        maxx=1.0,
        minx=0.0,
        maxy=1.0,
        miny=0.0,
        major_step=0.1,
        minor_step=0.01,
        res=2000
    )

    grid.show()

    key_point_9020 = np.array([[505.4134,     -291.54833333]])
    print(f'Key points on reference: {key_point_9020[0, 0]}, {key_point_9020[0, 1]}')
    key_point_9020[0, 0] -= src_min_x
    key_point_9020[0, 1] -= src_min_y
    key_point_9020[0, 0] /= src_max_x
    key_point_9020[0, 1] /= src_max_y

    x_prime, y_prime = TPS_project(g=g2,
                                   x=key_point_9020[0, 0],
                                   y=key_point_9020[0, 1])

    x_prime *= dst_max_x
    y_prime *= dst_max_y
    x_prime += dst_min_x
    y_prime += dst_min_y

    print(f'Key points on 5134: {x_prime}, {y_prime}')

    '''
    Q5134 key points
    [ 980.2344     -290.96233333]
    [ 955.9024      189.19366667]
    [ 898.0714      345.03766667]
    [ 837.8264      380.75566667]
    [ 646.1634      380.51866667]
    [ 586.0064      344.65266667]
    [ 528.5594      188.66666667] 
    [ 505.4134     -291.54833333]]
    '''

    '''
    Q9020 key points
    [[1242.60922196  251.7639571 ]
    [1220.10922196  648.9019571 ]
    [1180.76922196  846.5749571 ]
    [1080.10422196  886.7329571 ]
    [ 875.16722196  886.7329571 ]
    [ 774.50222196  846.5749571 ]
    [ 735.16222196  648.9019571 ]
    [ 712.66222196  251.7639571 ]]
    '''
