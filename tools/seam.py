import os.path as osp
import re

import numpy as np


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

    def __find_seam(self, arr: np.ndarray):
        found_j, found_idx = None, None
        for array, rev in zip([arr, arr[::-1, :]], [False, True]):
            _arr = [float(str(x)[:str(x).find('.') + Seam.FLOAT_2_STRING_PRECISION]) for x in array.flatten().tolist()]
            reverse = rev
            arr_start = _arr[:2]
            arr_end = _arr[-2:]

            for j, item in enumerate(self.seams):
                for idx, x in enumerate(item):

                    x_start = x[:2]
                    x_end = x[-2:]

                    starts_equal = [x_s == a_s for x_s, a_s in zip(x_start, arr_start)]
                    ends_equal = [x_s == a_s for x_s, a_s in zip(x_end, arr_end)]
                    start = all(starts_equal)
                    end = all(ends_equal)
                    if start and end:
                        found_j = j
                        found_idx = idx
                        print(j)
                        print(idx)
                        # den eimai sigouros an prepei na to epistrefw edw
                        return found_j, found_idx, reverse
        return None

    def export_to_file(self, target_file: str):
        s = ''
        for seam in self.seams_copy:
            s += str(seam) + '\n'
        with open(osp.join(self.pattern_path, target_file), 'w') as f:
            f.write(s)

    def replace(self, curve: np.ndarray):
        found_j, found_idx, reverse = self.__find_seam(curve)
        if found_j is None or found_idx is None:
            raise ValueError('The curve you are looking for is not found within the seams file.')
        else:
            if not reverse:
                self.seams[found_j][found_idx][2:-2] = [float(str(x)[:str(x).find('.') + Seam.FLOAT_2_STRING_PRECISION])
                                                        for
                                                        x in curve.flatten().tolist()[2:-2]]
                self.seams_copy[found_j][found_idx][2:-2] = curve.flatten().tolist()[2:-2]
            else:
                self.seams[found_j][found_idx][2:-2] = [float(str(x)[:str(x).find('.') + Seam.FLOAT_2_STRING_PRECISION])
                                                        for
                                                        x in reversed(curve.flatten().tolist()[2:-2])]
                self.seams_copy[found_j][found_idx][2:-2] = reversed(curve.flatten().tolist()[2:-2])


if __name__ == '__main__':
    GARMENT_DIR = '/home/kaseris/Documents/database/blouse/b1/Q6431'
    seam = Seam(GARMENT_DIR)
    print(seam[0, 3])

    arr = np.array([[248.5298, -86.4182],
                    [247.67538166, -86.47447046],
                    [370.72878248, -234.28576413],
                    [369.5598, -236.3522]])

    seam.replace(arr)
    print(seam[0, 3])
    seam.export_to_file('seam1.txt')
