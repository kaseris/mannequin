import os
import os.path as osp
import re

import numpy as np

from mannequin.detection import detect_keypoints
from mannequin.primitives.utils import sort_xy


class Seam:
    FLOAT_2_STRING_PRECISION = 3

    def __init__(self, pattern_path):
        self.pattern_path = pattern_path
        self.seams = []
        self.seams_copy = []
        self.read()

    def __getitem__(self, pos):
        idx_seam, idx_connection = pos
        return self.seams_copy[idx_seam][idx_connection]

    def read(self):
        with open(osp.join(self.pattern_path, 'seam.txt'), 'r') as f:
            for line in f:
                m = re.findall('\[[^\]]*\]', line.strip())
                # metatropi se float kapoias sygkekrimenis akribeias
                m = [item.replace('[', '') for item in m]
                m = [item.replace(']', '') for item in m]
                connections = []
                connections_copy = []
                for item in m:
                    item = item.split(', ')
                    connections.append([float(h[:h.find('.') + Seam.FLOAT_2_STRING_PRECISION]) for h in item])
                    connections_copy.append([float(h) for h in item])
                self.seams.append(connections)
                self.seams_copy.append(connections_copy)

    def __find_seam(self, curve: np.ndarray):
        def find_nearest(array, value):
            dist = array - value
            norm = np.linalg.norm(dist, axis=1)
            return norm.argmin(), norm.min()

        min_total_distance = 1e+6
        found_sublist = None
        found_seam = None
        for idx_ps, pattern_seam in enumerate(self.seams_copy):
            for idx_seam, seam in enumerate(pattern_seam):
                seam_array = np.asarray([[float(h1), float(h2)] for h1, h2 in zip(seam[::2], seam[1::2])])
                curve_start = curve[0, :]
                curve_end = curve[-1, :]

                distance_start = find_nearest(seam_array, curve_start)
                distance_end = find_nearest(seam_array, curve_end)

                total_distance = distance_start[1] + distance_end[1]
                index_pair = (distance_start[0], distance_end[0])
                reverse = False
                if total_distance < min_total_distance:
                    min_total_distance = total_distance
                    found_sublist = idx_ps
                    found_seam = idx_seam
                    reverse = True if index_pair[0] > index_pair[1] else False
        return found_seam, found_sublist, reverse

    def export_to_file(self, dst_path, target_file: str):
        s = ''
        for seam in self.seams_copy:
            s += str(seam) + '\n'

        if osp.exists(osp.join(dst_path, target_file)):
            os.remove(osp.join(dst_path, target_file))
        with open(osp.join(dst_path, target_file), 'w') as f:
            f.write(s)

    def replace(self, curve: np.ndarray):
        found_idx, found_j, reverse = self.__find_seam(curve)

        def find_nearest(array, value):
            dist = array - value
            norm = np.linalg.norm(dist, axis=1)
            return norm.argmin()

        arr = np.asarray([[x, y] for x, y in zip(self.seams_copy[found_j][found_idx][::2],
                                                 self.seams_copy[found_j][found_idx][1::2])])
        idx_start = find_nearest(arr, curve[0])
        idx_end = find_nearest(arr, curve[-1])

        if idx_start < idx_end:
            self.seams_copy[found_j][found_idx][2:-2] = curve.flatten().tolist()[2:-2]
        else:
            self.seams_copy[found_j][found_idx][2:-2] = curve[::-1].flatten().tolist()[2:-2]

    def __rearrange(self, array):
        key_points = detect_keypoints(array)
        sorted_keypoints = sort_xy(key_points)
        idx_sorted_by_y_front = np.argsort(sorted_keypoints[:, 1])[:2]
        lowest_points_front = sorted_keypoints[idx_sorted_by_y_front]
        where_max_X_front = np.argmax(lowest_points_front[:, 0])

        # Find the index of the lower-right point in the keypoints array
        # We store it in the idx_key_point_start var
        coords_key_point_start_front = lowest_points_front[where_max_X_front]
        idx_key_point_start_front = np.where(np.all(sorted_keypoints == coords_key_point_start_front,
                                                    axis=1))[0][0]
        idx = int(np.where(np.all(sorted_keypoints[idx_key_point_start_front] == array, axis=1))[0][0])
        part1 = array[:idx + 1]
        return np.vstack((array[idx:], part1))


if __name__ == '__main__':
    GARMENT_DIR = '/home/kaseris/Documents/database/blouse/b1/Q6431'
    seam = Seam(GARMENT_DIR)
    print(seam[0, 3])

    arr = np.array([[864.23910136, 342.86098836],
                    [7.67538166, -6.47447046],
                    [0.72878248, -4.28576413],
                    [844.44910136, 727.04698836]])

    seam.replace(arr)
    print(seam[0, 3])
    seam.export_to_file('_____seam.txt')
