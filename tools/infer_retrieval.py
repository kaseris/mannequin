import logging
import os.path as osp
from os import PathLike
import pickle

import numpy as np
import open3d as o3d
import torch

from typing import Union, Any

from model import PointNetCls

from mannequin.retrieval2d.retrieval_dimis import *


def resample_point_cloud(points, n_points):
    choice = np.random.choice(len(points), n_points, replace=True)
    return points[choice, :]


def infer(query, k, gallery_paths, object_type='image'):
    if object_type == 'image':
        return infer_2d(query, k, gallery_paths)
    else:
        return infer_3d(query, retrieval_k=k)


def infer_2d(query_img: Union[str, PathLike], k, gallery_paths):
    extractor = load_test_model()
    deep_feats, color_feats, labels = load_feat_db()
    clf = load_kmeans_model()

    f = dump_single_feature(query_img, extractor)

    result, ind = naive_query(f, deep_feats, color_feats, gallery_paths, k)
    return result, ind


def infer_3d(model: Union[str, PathLike],
          n_points=2500,
          feature_transform=False,
          model_path='/home/kaseris/Documents/pointnet.pytorch/utils/cls/cls_model_99.pth',
          embeddings_path='/home/kaseris/Documents/database/embeddings',
          retrieval_k=4) -> Any:
    pcd = o3d.io.read_triangle_mesh(model)
    pcd = np.asarray(pcd.vertices)
    print(pcd)
    logging.basicConfig(level=logging.DEBUG)

    pcd_resampled = resample_point_cloud(pcd, n_points)

    # Move point cloud to center
    point_set = pcd_resampled - np.expand_dims(np.mean(pcd_resampled, axis=0), 0)
    # Scale
    dist = np.max(np.sqrt(np.sum(point_set ** 2, axis=1)), 0)
    point_set = point_set / dist  # scale

    point_set = torch.from_numpy(point_set.astype(np.float32))

    model = PointNetCls(k=9,
                        feature_transform=feature_transform)
    logging.info('Loading model')
    state_dict = torch.load(model_path)
    model.load_state_dict(state_dict)
    # Set the model to eval mode
    model.eval().cuda()

    logging.info(f'point_set type: {point_set}')
    logging.info(f'point_set size: {point_set.size()}')

    with torch.no_grad():
        pred, trans, trans_feat, glob_feat = model(point_set.unsqueeze(0).permute(0, 2, 1).cuda())

    logging.info(f'glob_Feat size: {glob_feat.size()}')

    # Perform search
    # Loading database embeddings
    logging.info('Loading database')
    with open(osp.join(embeddings_path, 'embeddings.pkl'), 'rb') as f:
        gallery = pickle.load(f)

    with open(osp.join(embeddings_path, 'path_list.pkl'), 'rb') as f:
        paths = pickle.load(f)

    gallery = torch.from_numpy(gallery)
    dists = (-1.0) * torch.cdist(glob_feat.cpu(), gallery)
    _, idx = torch.topk(dists, k=retrieval_k+1)
    retrieved = [paths[i] for i in idx[0][1:]]
    print(retrieved)
    return retrieved, idx[0][1:].tolist()


if __name__ == '__main__':
    infer('/home/kaseris/Documents/Q9417.obj')
