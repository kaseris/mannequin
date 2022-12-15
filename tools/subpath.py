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

    def __find_seam(self, curve: np.ndarray, rearrange=False):

        def find_nearest(array, value):
            dist = array - value
            norm = np.linalg.norm(dist, axis=1)
            return norm.argmin(), norm.min()

        dist_idx_pair_start = []
        dist_idx_pair_end = []
        for idx, subpath in enumerate(self.subpath_copy):
            curve_start = curve[0, :]
            curve_end = curve[-1, :]
            if rearrange:
                dist_idx_pair_start.append(find_nearest(self.__rearrange(subpath), curve_start))
                dist_idx_pair_end.append(find_nearest(self.__rearrange(subpath), curve_end))
            else:
                dist_idx_pair_start.append(find_nearest(subpath, curve_start))
                dist_idx_pair_end.append(find_nearest(subpath, curve_end))

        dist_idx_pair_start_arr = np.asarray(dist_idx_pair_start)

        subpath_i = dist_idx_pair_start_arr[:, 1].argmin()

        return subpath_i, dist_idx_pair_start[subpath_i][0], dist_idx_pair_end[subpath_i][0]

    def replace(self, curve: np.ndarray):

        def find_nearest(array, value):
            dist = array - value
            norm = np.linalg.norm(dist, axis=1)
            return norm.argmin()

        i_subpath, start, end = self.__find_seam(curve, rearrange=True)
        # Find the first element of the subpath
        subpath_0 = self.subpath_copy[i_subpath][0]
        key_point_1 = find_nearest(self.subpath_copy[i_subpath], curve[0])
        key_point_2 = find_nearest(self.subpath_copy[i_subpath], curve[-1])
        region_copy = copy.deepcopy(self.subpath_copy[i_subpath])

        region_copy[:key_point_1] = curve[1:key_point_1 + 1][::-1]
        new_region = np.vstack([region_copy[:key_point_1],
                                region_copy[key_point_1:key_point_2],
                                curve[key_point_1+1:][::-1],
                                region_copy[0]])
        d = False
        if subpath_0 not in detect_keypoints(self.subpath_copy[i_subpath]):
            self.subpath_copy[i_subpath] = new_region
        else:
            i_subpath, start, end = self.__find_seam(curve, rearrange=False)
            reverse = False
            if end < start:
                reverse = True
            amount_of_points_to_replace = abs(end - start) + 1
            indices = sorted(np.random.permutation([n for n in range(6, 45)])[:amount_of_points_to_replace - 10])
            curve_ = np.vstack((curve[:5], curve[indices], curve[-5:]))
        #
            region_copy = copy.deepcopy(self.subpath_copy[i_subpath])
            if reverse:
                idx_start = region_copy.shape[0] - end - 1
                idx_end = region_copy.shape[0] - start - 1
                region_copy = region_copy[::-1]
                region_copy_part1 = region_copy[:idx_end]
                region_copy_part2 = region_copy[idx_start:]
            else:
                region_copy_part1 = region_copy[:start]
                region_copy_part2 = region_copy[end + 1:]
            region_new = np.vstack((region_copy_part1, curve_, region_copy_part2))
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
    pass
