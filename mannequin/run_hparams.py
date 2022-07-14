import argparse
import os
import os.path as osp

import matplotlib.pyplot as plt
import numpy as np

import conf
from main import save_txt, read_coords_from_txt, enlarge_contour
from shape_context import ShapeContext
from TPS import TPS_generate, TPS_project


def plot_matching(pc1, pc2, lines, where):
    plt.rcParams['figure.figsize'] = (12, 12)
    plt.gca().set_aspect('equal')
    plt.scatter(pc1[:, 0], pc1[:, 1])
    plt.scatter(pc2[:, 0], pc2[:, 1])

    for line in lines:
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), 'k--')
    plt.legend(['reference', 'input'])
    plt.savefig(where)


def parse_args():
    parser = argparse.ArgumentParser(description='Shape context automation script parser.')
    # Experiment
    parser.add_argument('--save_dir', type=str, default='exp/')
    parser.add_argument('--n_exp', type=int, default=1)
    # Inputs
    parser.add_argument('--src', type=str, default='Q9020front-S_38.xyz')
    parser.add_argument('--target', type=str, default='Q5134front-S_M.xyz')
    # Sampling parameters
    parser.add_argument('--N_enlarge', type=int, default=20000)
    parser.add_argument('--subsample_to', type=int, default=32)
    # Shape context parameters
    parser.add_argument('--n_bins_r', type=int, default=1)
    parser.add_argument('--n_bins_theta', type=int, default=1)
    parser.add_argument('--r_inner', type=float, default=1e-1)
    parser.add_argument('--r_outer', type=float, default=1e+3)
    return parser.parse_args()


if __name__ == '__main__':
    cfg = parse_args()

    ENLARGE_CONTOUR_TO_N = cfg.N_enlarge
    SUBSAMPLED_SHAPE_N = cfg.subsample_to
    STEP = ENLARGE_CONTOUR_TO_N // SUBSAMPLED_SHAPE_N

    coords = read_coords_from_txt(osp.join(conf.DATA_DIR, cfg.src), delimiter=',')
    coords_target = read_coords_from_txt(osp.join(conf.DATA_DIR, cfg.target), delimiter=',')

    coords = np.vstack((coords, coords[0]))
    coords_target = np.vstack((coords_target, coords_target[0]))

    coords = enlarge_contour(coords, ENLARGE_CONTOUR_TO_N)
    coords_target = enlarge_contour(coords_target, ENLARGE_CONTOUR_TO_N)

    coords = coords[::STEP]
    coords_target = coords_target[::STEP]

    sc = ShapeContext(n_bins_r=cfg.n_bins_r,
                      n_bins_theta=cfg.n_bins_theta,
                      r_inner=cfg.r_inner,
                      r_outer=cfg.r_outer)

    P = sc.compute(coords)
    Q = sc.compute(coords_target)

    cost, indices = sc.diff(P=P, Q=Q)

    lines = []
    matches = dict()
    matches['src'] = []
    matches['matches'] = []
    for p1, q1 in indices:
        matches['src'].append(coords[p1])
        matches['matches'].append(coords_target[q1])
        lines.append([[coords[p1][0], coords[p1][1]], [coords_target[q1][0], coords_target[q1][1]]])

    save_path = os.getcwd() + '/' + cfg.save_dir + str(cfg.n_exp)
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    save_txt(f'{save_path}/src.txt', matches['src'])
    save_txt(f'{save_path}/matches.txt', matches['matches'])
    plot_matching(coords, coords_target, lines, where=f'{save_path}/matches_plot.png')

    src = [x.tolist() for x in matches['src']]
    dst = [x.tolist() for x in matches['matches']]

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

    key_points_ref = np.array([[1242.60922196, 251.7639571],
                               [1220.10922196, 648.9019571],
                               [1180.76922196, 846.5749571],
                               [1080.10422196, 886.7329571],
                               [875.16722196, 886.7329571],
                               [774.50222196, 846.5749571],
                               [735.16222196, 648.9019571],
                               [712.66222196, 251.7639571]])

    key_points_target = np.asarray(conf.KEYPOINTS_LABELS[cfg.target])

    estimated_key_points = []
    for i in range(key_points_ref.shape[0]):
        key_point_9020 = key_points_ref[i, :].copy()
        # print(f'Key points on reference: {key_point_9020[0]}, {key_point_9020[1]}')
        key_point_9020[0] -= src_min_x
        key_point_9020[1] -= src_min_y
        key_point_9020[0] /= src_max_x
        key_point_9020[1] /= src_max_y

        x_prime, y_prime = TPS_project(g=g2,
                                       x=key_point_9020[0],
                                       y=key_point_9020[1])

        x_prime *= dst_max_x
        y_prime *= dst_max_y
        x_prime += dst_min_x
        y_prime += dst_min_y

        # print(f'Key points on 5134: {x_prime}, {y_prime}')
        estimated_key_points.append([x_prime, y_prime])

    estimated_key_points = np.asarray(estimated_key_points)
    mse_X = np.sqrt((key_points_target[:, 0] - estimated_key_points[:, 0])**2)
    mse_X = np.mean(mse_X)
    mse_Y = np.sqrt((key_points_target[:, 1] - estimated_key_points[:, 1])**2)
    mse_Y = np.mean(mse_Y)

    mse = np.sum(np.sqrt((key_points_target - estimated_key_points)**2), axis=1)
    mse = np.mean(mse)

    perf = f'MSE Perfomance:\n'
    perf += f'MSE: {mse:.3f}\n'
    perf += f'MSE in X: {mse_X:.3f}\n'
    perf += f'MSE in Y: {mse_Y:.3f}\n'

    with open(f'{save_path}/perf.txt', 'w') as f:
        perf_metrics = f'========== Performance ==========\n'
        perf_metrics += f'Source pattern (reference): {cfg.src}\n'
        perf_metrics += f'Target pattern (input): {cfg.target}\n'
        perf_metrics += f'\nBending energy: {g2["be"]:.3f}\n'
        perf_metrics += f'Reference key points:\n'
        for point in key_points_ref:
            x, y = point
            perf_metrics += f'[ {str(x)}, {str(y)} ]\n'
        perf_metrics += '\n'
        perf_metrics += f'Ground truth target key points:\n'
        for point in key_points_target:
            x, y = point
            perf_metrics += f'[ {str(x)}, {str(y)} ]\n'
        perf_metrics += '\n'
        perf_metrics += f'Estimated key points:\n'
        for point in estimated_key_points:
            x, y = point
            perf_metrics += f'[ {str(x)}, {str(y)} ]\n'
        perf_metrics += '\n'
        perf_metrics += perf
        perf_metrics += '\nConfiguration:\n'
        perf_metrics += f'n_bins_r: {str(cfg.n_bins_r)}\n'
        perf_metrics += f'n_bins_theta: {str(cfg.n_bins_theta)}\n'
        perf_metrics += f'r_inner: {str(cfg.r_inner)}\n'
        perf_metrics += f'r_outer: {str(cfg.r_outer)}\n'
        perf_metrics += f'N_enlarge: {str(cfg.N_enlarge)}\n'
        perf_metrics += f'subsample_to: {str(cfg.subsample_to)}'
        f.write(perf_metrics)
