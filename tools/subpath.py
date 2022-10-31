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
                self.subpath_copy.append([float(num) for num in nums])

    def __find_seam(self, arr: np.ndarray):
        for array, rev in zip([arr, arr[::-1, :]], [False, True]):
            start = array[0, :]
            end = array[-1, :]
            j_start, j_end, i_subpath = None, None, None
            for i, path in enumerate(self.subpath):

                pairs = [[path[i], path[i + 1]] for i in range(0, len(path) - 1, 2)]
                for j, pair in enumerate(pairs):
                    if np.allclose(start, pair):
                        print(f'vrika thn arxh ths kampylis sto: {j} ({pair})')
                        j_start = j
                        i_subpath = i
                    elif np.allclose(end, pair):
                        print(f'vrika to telos ths kampylis sto: {j} ({pair})')
                        j_end = j
        return j_start, j_end, i_subpath

    def replace(self, curve: np.ndarray):
        j_start, j_end, i_subpath = self.__find_seam(curve)
        sp = self.subpath_copy[i_subpath]
        part_1 = sp[:2 * ((j_start - 1) + 1)]
        part_2 = curve.flatten().tolist()
        part_3 = sp[2 * (j_end+1):]
        self.subpath_copy[i_subpath] = part_1 + part_2 + part_3

    def export_to_file(self, target_filename):
        s = ''
        for seam in self.subpath_copy:
            s += str(seam) + '\n'
        with open(osp.join(self.garment_path, target_filename), 'w') as f:
            f.write(s)


if __name__ == '__main__':
    subpath = SubPath('/home/kaseris/Documents/database/blouse/b1/Q6431')
    arr = np.array([[1166.37770136, 658.81548836], [1.08370136, 1.13748836], [1171.59270136, 661.80148836]])
    subpath.replace(arr)
    subpath.export_to_file('subpath1.txt')
