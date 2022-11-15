import copy
import os
import os.path as osp

import numpy as np

from mannequin.fileio import read_coords_from_txt


class IndividualPattern:

    pattern_files = ['front.xyz', 'back.xyz', 'skirt back.xyz', 'skirt front.xyz', 'sleever.xyz', 'sleevel.xyz',
                     'cuffl.xyz', 'cuffr.xyz', 'collar.xyz']

    def __init__(self, garment_dir):
        self.garment_dir = garment_dir

        self.__patterns = dict()
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
                    self.__patterns[f.replace('.xyz', '')] = read_coords_from_txt(osp.join(ind_patterns, f),
                                                                                  delimiter=',')

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
        idx_start = find_nearest(coords_region, curve_start)
        idx_end = find_nearest(coords_region, curve_end)
        if idx_end < idx_start:
            reverse = True

        if reverse:
            curve = curve[::-1]
        region_copy = copy.deepcopy(self[region])
        region_copy_part1 = region_copy[:idx_start]
        region_copy_part2 = region_copy[idx_end+1:]
        region_new = np.vstack((region_copy_part1, curve, region_copy_part2))
        self.replace_region(region, region_new)

    @property
    def patterns(self):
        return self.__patterns

    def replace_region(self, region, curve):
        self.__patterns[region] = curve

    def __getitem__(self, item):
        if item not in [l.replace('.xyz', '') for l in IndividualPattern.pattern_files]:
            raise KeyError(f'{item}')
        return self.__patterns[item]


if __name__ == '__main__':
    pass