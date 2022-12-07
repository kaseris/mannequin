import copy
import os
import os.path as osp

import numpy as np

from mannequin.detection import detect_keypoints
from mannequin.fileio import read_coords_from_txt
from mannequin.primitives.utils import sort_xy


class IndividualPattern:

    pattern_files = ['front.xyz', 'back.xyz', 'skirt back.xyz', 'skirt front.xyz', 'sleever.xyz', 'sleevel.xyz',
                     'cuffl.xyz', 'cuffr.xyz', 'collar.xyz']

    def __init__(self, garment_dir):
        self.garment_dir = garment_dir

        self.__patterns = dict()
        self.__parts = []
        self.__flags = {'armhole': False,
                        'collar': False}
        self.__build()

    def __build(self):
        if not osp.isdir(self.garment_dir):
            raise FileNotFoundError(f'`{self.garment_dir}` is not a directory')
        else:
            children = os.listdir(self.garment_dir)
            if not 'individual patterns' in children:
                raise FileNotFoundError(f'`individual patterns` directory was not found in this folder.')

            ind_patterns = osp.join(self.garment_dir, 'individual patterns')
            for f in IndividualPattern.pattern_files:
                if f in os.listdir(ind_patterns):
                    self.__patterns[f.replace('.xyz', '')] = self.__rearrange(
                        read_coords_from_txt(osp.join(ind_patterns, f),
                                             delimiter=','))
            with open(osp.join(self.garment_dir, 'category.txt'), 'r') as f:
                for line in f:
                    self.__parts.append(line.strip()[3:-3])

        for part in self.__parts:
            if 'sleeve' in part:
                self.__flags['armhole'] = True
            elif 'collar' in part:
                self.__flags['collar'] = True

    def replace(self, curve, region):
        def find_nearest(array, value):
            dist = array - value
            norm = np.linalg.norm(dist, axis=1)
            return norm.argmin()
        coords_region = self[region]
        reverse = False
        # Find if CW/CCW
        curve_start = curve[0, :]
        curve_end = curve[-1, :]
        idx_start_ = find_nearest(coords_region, curve_start)
        idx_end_ = find_nearest(coords_region, curve_end)
        if idx_end_ < idx_start_:
            reverse = True

        region_copy = copy.deepcopy(self[region])
        if reverse:
            idx_start = region_copy.shape[0] - idx_end_ - 1
            idx_end = region_copy.shape[0] - idx_start_ - 1
            region_copy = region_copy[::-1]
            region_copy_part1 = region_copy[:idx_end]
            region_copy_part2 = region_copy[idx_start:]
        else:
            region_copy_part1 = region_copy[:idx_start_]
            region_copy_part2 = region_copy[idx_end_+1:]
        region_new = np.vstack((region_copy_part1, curve, region_copy_part2))
        self.replace_region(region, region_new)

    @property
    def patterns(self):
        return self.__patterns

    def replace_region(self, region, curve):
        self.__patterns[region] = curve

    def get_flag(self, choice):
        return self.__flags[choice]

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

    def add_alternative_curves(self, curves):
        for idx, curve in enumerate(curves):
            k = f'alternative_{idx}'
            self.__patterns[k] = curve

    def __getitem__(self, item):
        # if item not in [l.replace('.xyz', '') for l in IndividualPattern.pattern_files]:
        #     raise KeyError(f'{item}')
        return self.__patterns[item]


if __name__ == '__main__':
    pass
