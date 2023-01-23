import os
import re

import numpy as np


def read_seam_structure(garment_dir):
    structure = dict()
    category_data = []

    print('Reading category.txt')
    # TODO: Need to change the hard-coded directory.
    with open(f'{garment_dir}/category.txt', 'r') as f:
        for line in f:
            line = line.strip()
            line_after = re.sub("\[\['|']]", "", line)
            category_data.append(line_after)
            structure[line_after] = dict()

    print('Reading connections.txt')
    # TODO: Need to change the hard-coded directory.
    with open(f'{garment_dir}/connections.txt', 'r') as f:
        for line_number, line in enumerate(f):
            line = line.strip().split()

            structure[category_data[line_number]]['connections'] = []
            for idx, l in enumerate(line):
                l_after = re.sub("\[\['|']]|']|\['|,", "", l)
                # print(f'ln_number: {line_number}, idx: {idx}, line content: {l_after}')
                structure[category_data[line_number]]['connections'].append(l_after)

    print('Reading seams.txt')
    # TODO: Need to change the hard-coded directory.
    with open(f'{garment_dir}/seam.txt', 'r') as f:
        for line_number, line in enumerate(f):
            line_split = re.split("\[|]", line)
            line_split = [i
                              .replace(' ', '')
                              .split(',')
                          for i in line_split if i not in ['', '\n', ', ']]
            structure[category_data[line_number]]['seams'] = line_split

    return structure


def write_array_as_ind_pat(fname, array):
    with open(fname, 'w') as f:
        for point in array:
            x, y = point
            f.write(f'{str(x)},0.0,{str(y)}')


def save_txt(fname, obj):
    with open(fname, 'w') as f:
        for point in obj:
            x, y = point
            f.write(f'{str(x)},{str(y)}\n')


def read_coords_from_txt(path, delimiter=' '):
    coords = []
    with open(path, 'r') as f:
        for idx, line in enumerate(f):
            line = line.split(delimiter)
            x, y = float(line[0]), float(line[-1])
            coords.append([x, y])
    return np.asarray(coords)


def check_vert(line: str):
    r"""Indicates the presence of a vertex in an OBJ file's line.

    Args:
        :param line: (str) A file's line.
    Returns:
        True if a vertex is contained in a line, otherwise False.
    """
    return True if line.strip().split(' ')[0] == 'v' else False


def strip_split(str_arg: str):
    r"""Returns a string list, starting from the second element of the line,
    removing newline escape chars."""
    return str_arg.strip().split(' ')[1:]


def make_float(l: list):
    r"""Converts a numeric list of strings to float."""
    return [float(i) for i in l]


def read_obj(filename):
    r"""Reads a Wavefront OBJ file and returns ONLY its vertices."""
    with open(filename, 'r') as f:
        ln = f.readlines()
        verts = map(strip_split, list(filter(check_vert, ln)))

    verts = list(map(make_float, verts))
    return verts


def check_obj(filename: str):
    return filename.endswith('.obj')


if __name__ == '__main__':
    pass
