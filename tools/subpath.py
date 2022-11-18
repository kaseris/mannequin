import copy
import os
import os.path as osp
import re

import numpy as np


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

        if reverse:
            curve = curve[::-1]

        amount_of_points_to_replace = abs(end - start) + 1
        indices = sorted(np.random.permutation([n for n in range(6, 45)])[:amount_of_points_to_replace - 10])
        curve_ = np.vstack((curve[:5], curve[indices], curve[-5:]))

        region_copy = copy.deepcopy(self.subpath_copy[i_subpath])
        region_copy_part1 = region_copy[:start + 1]
        region_copy_part2 = region_copy[end:]
        region_new = np.vstack((region_copy_part1, curve_[1:-1], region_copy_part2))
        self.subpath_copy[i_subpath] = region_new

    def export_to_file(self, dst_path, target_filename):
        s = ''
        for idx, seam in enumerate(self.subpath_copy):
            l2 = [f'{n:.8f}' for n in seam.flatten()]
            s += '[' + f', '.join(l2) + ']'
            if idx < len(self.subpath_copy):
                s += '\n'
        if osp.exists(osp.join(dst_path, target_filename)):
            os.remove(osp.join(dst_path, target_filename))

        with open(osp.join(dst_path, target_filename), 'w') as f:
            f.write(s)


if __name__ == '__main__':
    subpath = SubPath('/home/kaseris/Documents/database/blouse/b1/Q6431')
    arr = np.array([[1166.37770136, 658.81548836], [1.08370136, 1.13748836], [1171.59270136, 661.80148836]])
    subpath.replace(arr)
    subpath.export_to_file('___subpath1.txt')
