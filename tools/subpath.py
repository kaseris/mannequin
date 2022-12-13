import copy
import os
import os.path as osp
import re

import numpy as np

from mannequin.primitives.utils import sort_xy
from mannequin.detection import detect_keypoints


class SubPath:

    FLOAT_2_STRING_PRECISION = 3

    def __init__(self, garment_path):
        self.subpath = []
        self.subpath_copy = []
        self.garment_path = garment_path
        self.read()

    def __getitem__(self, pos):
        return self.subpath_copy[pos]

    def read(self):
        with open(osp.join(self.garment_path, 'subpath.txt'), 'r') as f:
            for line in f:
                line = re.sub('\[|]', '', line.strip())
                nums = line.split(', ')
                self.subpath.append([float(num[:num.find('.') + SubPath.FLOAT_2_STRING_PRECISION]) for num in nums])
                self.subpath_copy.append(np.asarray([[float(n1), float(n2)] for n1, n2 in zip(nums[::2], nums[1::2])]))

    def __find_seam(self, curve: np.ndarray):

        def find_nearest(array, value):
            dist = array - value
            norm = np.linalg.norm(dist, axis=1)
            return norm.argmin(), norm.min()

        dist_idx_pair_start = []
        dist_idx_pair_end = []
        for idx, subpath in enumerate(self.subpath_copy):
            curve_start = curve[0, :]
            curve_end = curve[-1, :]
            # dist_idx_pair_start.append(find_nearest(self.__rearrange(subpath), curve_start))
            # dist_idx_pair_end.append(find_nearest(self.__rearrange(subpath), curve_end))
            dist_idx_pair_start.append(find_nearest(subpath, curve_start))
            dist_idx_pair_end.append(find_nearest(subpath, curve_end))

        dist_idx_pair_start_arr = np.asarray(dist_idx_pair_start)

        subpath_i = dist_idx_pair_start_arr[:, 1].argmin()

        return subpath_i, dist_idx_pair_start[subpath_i][0], dist_idx_pair_end[subpath_i][0]

    def replace(self, curve: np.ndarray):
        i_subpath, start, end = self.__find_seam(curve)
        reverse = False
        if end < start:
            reverse = True

        # if reverse:
        #     curve = curve[::-1]

        # amount_of_points_to_replace = abs(end - start) + 1
        # indices = sorted(np.random.permutation([n for n in range(6, 45)])[:amount_of_points_to_replace - 10])
        # curve_ = np.vstack((curve[:5], curve[indices], curve[-5:]))

        region_copy = copy.deepcopy(self.subpath_copy[i_subpath])
        # region_copy = copy.deepcopy(self.__rearrange(self.subpath_copy[i_subpath]))
        if reverse:
            idx_start = region_copy.shape[0] - end - 1
            idx_end = region_copy.shape[0] - start - 1
            region_copy = region_copy[::-1]
            region_copy_part1 = region_copy[:idx_end]
            region_copy_part2 = region_copy[idx_start:]
        else:
            region_copy_part1 = region_copy[:start]
            region_copy_part2 = region_copy[end + 1:]
        region_new = np.vstack((region_copy_part1, curve[::4], region_copy_part2))
        if reverse:
            region_new = region_new[::-1]
        self.subpath_copy[i_subpath] = region_new

    def export_to_file(self, dst_path, target_filename):
        s = ''
        for idx, seam in enumerate(self.subpath_copy):
            l2 = [f'{n}' for n in seam.flatten()]
            s += '[' + f', '.join(l2) + ']'
            if idx < len(self.subpath_copy):
                s += '\n'
        if osp.exists(osp.join(dst_path, target_filename)):
            os.remove(osp.join(dst_path, target_filename))

        with open(osp.join(dst_path, target_filename), 'w') as f:
            f.write(s)

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
    subpath = SubPath('/home/kaseris/Documents/database/dress/d1/Q6089')
    arr = np.array([[1390.93660, 442.51290],
                    [1385.28940, 439.51441],
                    [1381.37521, 434.07325],
                    [1377.74092, 426.52733],
                    [1374.59719, 418.33737],
                    [1372.43615, 409.50850],
                    [1371.42020, 399.27025],
                    [1371.26502, 387.10205],
                    [1371.32558, 373.16538],
                    [1370.85227, 358.26149],
                    [1369.26430, 343.49519],
                    [1366.29108, 329.85372],
                    [1361.95202, 317.91640],
                    [1356.44289, 307.79516],
                    [1350.01405, 299.25814],
                    [1342.88978, 291.92509],
                    [1335.23580, 285.44590],
                    [1327.16202, 279.61903],
                    [1318.74498, 274.43380],
                    [1310.05653, 270.03248],
                    [1301.18520, 266.60442],
                    [1292.23849, 264.25284],
                    [1283.32133, 262.89938],
                    [1274.50106, 262.28672],
                    [1265.78077, 262.09162],
                    [1257.10229, 262.09165],
                    [1248.38222, 262.28681],
                    [1239.56237, 262.89953],
                    [1230.64579, 264.25306],
                    [1221.69974, 266.60473],
                    [1212.82907, 270.03292],
                    [1204.14118, 274.43441],
                    [1195.72456, 279.61983],
                    [1187.65098, 285.44691],
                    [1179.99702, 291.92630],
                    [1172.87263, 299.25954],
                    [1166.44361, 307.79673],
                    [1160.93432, 317.91809],
                    [1156.59518, 329.85550],
                    [1153.62194, 343.49701],
                    [1152.03400, 358.26328],
                    [1151.56064, 373.16705],
                    [1151.62101, 387.10348],
                    [1151.46553, 399.27136],
                    [1150.44925, 409.50924],
                    [1148.28803, 418.33780],
                    [1145.14433, 426.52756],
                    [1141.51016, 434.07338],
                    [1137.59594, 439.51448],
                    [1131.94860, 442.51290]]
                   )
    subpath.replace(arr)
    subpath.export_to_file('/home/kaseris/Documents/database/dress/d1/Q6089', '___subpath1.txt')
