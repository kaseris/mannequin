import logging
from os import PathLike

import numpy as np
import open3d as o3d
import torch
import torch.utils.data as data

from typing import Union, Any

from model import PointNetCls


def infer(model: Union[str, PathLike]) -> Any:
    pcd = o3d.io.read_point_cloud(model)
    pcd = np.asarray(pcd.points)

    logging.debug(f'pcd type: {type(pcd)}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)