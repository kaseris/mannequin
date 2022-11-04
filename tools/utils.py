import os.path as osp

import numpy as np


def get_model_name(path_to_obj):
    n1, n2 = osp.splitext(path_to_obj)
    filename = osp.basename(n1)
    return filename.split('_')[0]


def similarity(query, retrieved, ss_mat):
    if ss_mat[retrieved, query] <= 0.0:
        return ss_mat[query, retrieved]
    return ss_mat[retrieved, query]


def create_ss_matrix(path):
    with open(path, 'r') as f:
        for idx, line in enumerate(f):
            l = line.strip().split(',')
            if idx == 0:
                ss = np.zeros((len(l) + 1, len(l) + 1))
            ss[idx, idx + 1:] = [float(el) for el in l]
    return ss
