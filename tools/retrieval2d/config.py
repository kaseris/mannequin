# -*- coding: utf-8 -*-
from torch.cuda import is_available
import cfg

GPU_ID = 'cuda' if is_available() else 'cpu'
TRAIN_BATCH_SIZE = 32
TEST_BATCH_SIZE = 32
TRIPLET_BATCH_SIZE = 32
EXTRACT_BATCH_SIZE = 64
TEST_BATCH_COUNT = 30
NUM_WORKERS = 4
LR = 0.001
MOMENTUM = 0.5
EPOCH = 10
DUMPED_MODEL = f"{cfg.DATABASE_DIR}/embeddings/models/model_10_final.pth.tar"

LOG_INTERVAL = 10
DUMP_INTERVAL = 500
TEST_INTERVAL = 100

DATASET_BASE = r'/home/kaseris/Documents/fir/Category_and_Attribute_Prediction'
DIMIS_DATASET_BASE = 'C:/Users/kaseris/Documents/mannequin/database'
ENABLE_INSHOP_DATASET = False
INSHOP_DATASET_PRECENT = 0.8
IMG_SIZE = 256
CROP_SIZE = 224
INTER_DIM = 512
CATEGORIES = 20
N_CLUSTERS = 3
COLOR_TOP_N = 2
TRIPLET_WEIGHT = 2.0
ENABLE_TRIPLET_WITH_COSINE = False  # Buggy when backward...
COLOR_WEIGHT = 0.0
DISTANCE_METRIC = ('euclidean', 'cosine')
FREEZE_PARAM = False
EMBEDDINGS_DIR = f'{cfg.DATABASE_DIR}/embeddings'