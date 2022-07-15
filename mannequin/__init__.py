import os
import os.path as osp
import json

from pathlib import Path

from .detection import *
from .fileio import *
from .lerp import *
from .primitives import *
from .retrieval3d import *
# from .TPS import *

PATH = osp.dirname(osp.abspath(__file__))

with open(osp.join(PATH, 'conf.json')) as f:
    d = json.load(f)

MNQ_DATASETS = d['datasets']
MNQ_3DPC_DATASET_BASE_DIR = Path(MNQ_DATASETS['3DGarments'])
MNQ_3DPC_DATASET_CLUSTERS_DIR = osp.join(PATH, MNQ_DATASETS['clusters'])
MNQ_3DPC_DATASET_GLOBAL_DESCRIPTORS = osp.join(PATH, MNQ_DATASETS['global_descriptors'])
