import math
import os
import os.path as osp
import re

from pathlib import Path

import numpy as np

from seam import Seam

FLOAT_2_STRING_PRECISION = 3

rules_blouse = {'armhole': {8: ['1', '5'],
                            6: ['1', '3'],
                            -1: ['1', '7']},
                'collar': {8: ['3'],
                           6: ['2'],
                           -1: ['4']},
                'sleeve': {5: ['0', '4'],
                           6: ['0', '4'],
                           3: ['0', '2']}
                }


def sleeves_exist(dirname_to_garment):
    data_dir = osp.join(dirname_to_garment, 'data/txt')
    return any(['sleeve' in part for part in os.listdir(data_dir)])


def angle(s1, s2):
    return math.degrees(math.atan((s2 - s1) / (1 + (s2 * s1))))


def distance_bez_to_bez(bezier):
    return np.linalg.norm(bezier[0] - bezier[-1])


def slope(x1, y1, x2, y2):
    # Line slope given two points:
    return (y2 - y1) / (x2 - x1)


def scale_factor(bezier1, bezier2):
    d1 = distance_bez_to_bez(bezier1)
    d2 = distance_bez_to_bez(bezier2)
    return d1 / d2


def get_filename_for_bezier_points(dir_to_garment, pattern, n: str):
    fname = osp.join(dir_to_garment, f'data/txt/{pattern}', f'bezier_{pattern.replace(" ", "_")}_{n}.txt')
    if osp.exists(fname):
        return fname
    else:
        raise FileNotFoundError(f'File `{fname}` does not exist.')


def read_bezier_points_from_txt(fname):
    with open(fname, 'r') as f:
        coords = []
        for idx, line in enumerate(f):
            x, y = line.strip().split(',')
            coords.append([float(x), float(y)])
        return np.vstack(coords)


def read_entire_pattern(dir_to_garment, pattern):
    data_dir = osp.join(dir_to_garment, 'data/txt', pattern)
    bezier_files = [osp.join(data_dir, filename) for filename in sorted(os.listdir(data_dir))]
    return list(map(read_bezier_points_from_txt, bezier_files))


def rotate(coords, angle):
    angle_rad = np.deg2rad(angle)
    R = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                  [np.sin(angle_rad), np.cos(angle_rad)]])
    return np.dot(coords, R.T)


def get_keypoint_count(dir_to_garment, pattern):
    keypoints = len(os.listdir(osp.join(dir_to_garment, 'data', 'txt', pattern)))
    if keypoints in [8, 6, 5, 3]:
        return keypoints
    else:
        return -1


def visualize_points(points1, points2):
    import matplotlib.pyplot as plt
    plt.scatter(points1[:, 0], points1[:, 1])
    plt.scatter(points2[:, 0], points2[:, 1])
    plt.legend(['points1', 'points2'])
    plt.show()


def main(rouxo1, rouxo2, selection: str, pattern: str):
    #   TODO: na valw wraio onomataki gia to function
    # Diavazw 1o rouxo
    print('Ti theleis na allakseis?')
    print(f'Selection: {selection}')
    print(f'Number keypoints rouxo1: {get_keypoint_count(rouxo1, pattern=pattern)}')
    print(f'Number keypoints rouxo2: {get_keypoint_count(rouxo2, pattern=pattern)}')

    if not sleeves_exist(rouxo2):
        raise ValueError(f'Garment {Path(osp.basename(rouxo2)).name} does not contain sleeves.')

    # Prepei na kserw pio arxeio tha diabasw prwta
    # Tha xrisimopoihsw tous kanones
    # Points1: ta simeia twn bezier gia ta collar/sleeves tou prwtou rouxou: lista
    which1 = rules_blouse[selection][get_keypoint_count(rouxo1, pattern=pattern)]
    fnames1 = [get_filename_for_bezier_points(rouxo1, pattern, n=n) for n in which1]
    points1 = [read_bezier_points_from_txt(fname=f) for f in fnames1]
    # Points2: ta simeia twn bezier gia ta collar/sleeves tou deuterou rouxou: lista
    which2 = rules_blouse[selection][get_keypoint_count(rouxo2, pattern=pattern)]
    fnames2 = [get_filename_for_bezier_points(rouxo2, pattern, n=n) for n in which2]
    points2 = [read_bezier_points_from_txt(fname=f) for f in fnames2]

    # kano scaling wste to 2 na katsei sto 1
    sf = [scale_factor(b1, b2) for b1, b2 in zip(points1, points2)]
    #print(sf)
    # pollaplasiazw tis bezier tou 2 me ta scale factors
    points2_scaled = [pts * s for pts, s in zip(points2, sf)]

    points2_rot = []
    for ps1, ps2 in zip(points1, points2_scaled):
        line1 = (ps1[0], ps1[-1])
        line2 = (ps2[0], ps2[-1])
        slope1 = slope(line1[0][0], line1[0][1], line1[1][0], line1[1][1])
        slope2 = slope(line2[0][0], line2[0][1], line2[1][0], line2[1][1])
        # ypologizw thn gwnia pou sxhmatizetai metaksy twn dyo eytheiwn
        ang = angle(slope2, slope1)
        #print(ang)
        points2_rotated = rotate(ps2, angle=ang)
        points2_rot.append(points2_rotated)

    # Briskw poy prepei na pane ta manikia/collars tou 2ou ws pros to 1o
    # Briskw to prwto shmeio tis kampylis pou thelw na metakinisw
    x0y0 = points2_rot[0][0, :]
    # Briskw to prwto shmeio tis kampylis stin opoia thelei antikatastasi
    x0y0_prime = points1[0][0, :]

    translated_points = []
    for ps1, ps2 in zip(points1, points2_rot):
        # Briskw to dianysma poy koitaei apo thn arxh toy points2_rot pros thn arxi tou points1
        diff = ps2[0, :] - ps1[0, :]
        translated = ps2 - diff
        translated_points.append(translated)

    pc_rouxo1 = read_entire_pattern(rouxo1, pattern=pattern)
    pc_rouxo1_np = np.vstack(pc_rouxo1)

    # visualize_points(pc_rouxo1_np, translated_points[0])
    print(f'translated_points[1]: {translated_points[0]}')
    return translated_points


if __name__ == '__main__':
    # So far we replaced the armholes of the garment
    # Now to replace the sleeves themselves
    # We only care about the curvy part of the sleeve
    curves = main(rouxo1='/home/kaseris/Documents/database/blouse/b1/Q7180',
                  rouxo2='/home/kaseris/Documents/database/blouse/b1/Q6431',
                  selection='collar',
                  pattern='front')
    seam = Seam('/home/kaseris/Documents/database/blouse/b1/Q7180')
    for curve in curves:
        seam.replace(curve)

    seam.export_to_file('seam1.txt')
