import os
import os.path as osp
import random
import time

import numpy as np
import yaml

from pathlib import Path
from typing import Union, Iterable, List

from mannequin.fileio import check_obj
import mannequin.retrieval3d#.r3d import downsample_point_cloud, generate_point_cloud, generate_point_cloud_object, compute_fpfh

# Change the directory accordingly
DATASET_BASE_DIR = '/home/kaseris/Documents/3DGarments'


def make_categories(base_dir: Union[str, Path]) -> Iterable:
    categories = list(map(lambda x: x.strip().split('_'), os.listdir(base_dir)))
    categories = list(map(lambda x: ' '.join(x[:-1]), categories))
    return categories


def find_obj_dirs(base_dir: Union[str, Path]) -> List[Union[str, Path]]:
    objs = []
    for root, dirs, files in os.walk(base_dir):
        filenames = list(filter(lambda x: True if 'scan' not in x else False, list(filter(check_obj, files))))
        filenames = list(map(lambda x: osp.join(root, x), filenames))

        objs.append(filenames)
    filenames = list(filter(lambda x: not not x, objs))
    return [f[0] for f in filenames]


def randomize_dataset(dataset: List[Union[str, Path]],
                      num_samples: int = 1000):
    r"""Create a random dataset from its samples"""
    return random.sample(dataset, num_samples)


def make_dataset(base_dir: Union[str, Path],
                 num_samples: int = 1000) -> List[Union[str, Path]]:
    # Traverse the dataset directory and find the paths to the OBJ files
    obj_paths = find_obj_dirs(base_dir)
    # Create a smaller portion of the dataset with shuffled indices
    assert num_samples <= len(obj_paths), "`num_samples` must be smaller or equal than the dataset's length."
    return randomize_dataset(obj_paths, num_samples=num_samples)


class OBJDataset:
    """Dataset object for easy access and batch creation for point cloud data."""
    def __init__(self,
                 base_dir: Union[str, Path]):
        self.base_dir = base_dir
        self.dirs = find_obj_dirs(base_dir)

    def __getitem__(self, idx):
        return self.dirs[idx]

    def __len__(self):
        return len(self.dirs)


class OBJDataLoader:
    def __init__(self,
                 dataset: OBJDataset,
                 batch_size: int = 100,
                 shuffle: bool = True):
        self._dataset = dataset
        self._dataset_len = len(dataset)
        self.batch_size = batch_size
        self.shuffle = shuffle

        self.num = 0

    def __iter__(self):
        return self

    def __next__(self) -> np.ndarray:
        if self.num >= self._dataset_len - 1:
            raise StopIteration
        else:
            # self.num += self.batch_size
            start = self.num
            end = self.num + self.batch_size
            print(f'Start: {start}, end: {end}')
            _arr = self._collate_fn(start, end)
            self.num += self.batch_size
            return _arr

    def _collate_fn(self, start, end) -> np.ndarray:
        batch = self._dataset[start:end]
        fpfh_feat_list = []
        for element in batch:
            pc = retrieval3d.r3d.generate_point_cloud(element)
            pc = retrieval3d.r3d.generate_point_cloud_object(pc)
            pc = retrieval3d.r3d.downsample_point_cloud(pc, voxel_size=12.0)
            fpfh = retrieval3d.r3d.compute_fpfh(pc).T
            # print(fpfh)
            # fpfh_norm = fpfh / fpfh.sum(axis=1)[:, None]
            fpfh_feat_list.append(fpfh)
        return np.vstack(fpfh_feat_list)


if __name__ == '__main__':
    pass
