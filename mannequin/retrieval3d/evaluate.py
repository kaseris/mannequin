import os
from typing import List, Union
from pathlib import Path

import numpy as np

import mannequin as mnq


GARMENT_CATEGORIES = ['dress', 'skirt', 'tee', 'jumpsuit']
MODELS_PER_CATEGORY = {
    'jumpsuit': 2000,
    'skirt': 2600
}


def infer_class(retrieved: List):
    """Given an OBJ file path, what is its garment category?"""
    labels = []
    for path in retrieved:
        for cat in GARMENT_CATEGORIES:
            if cat in path:
                labels.append(cat)

    return labels

def recall(query_obj: str,
           retrieved: List[str]):
    for cat in GARMENT_CATEGORIES:
        if cat in query_obj:
            query_label = cat
    retrieved_labels = infer_class(retrieved)
    # Find the number of correct items that correspond to the query.
    # As a correct item, we define the retrieved item that belongs to the
    # same class as the query object.
    num_correct = len(list(filter(lambda x: x == query_label, retrieved_labels)))
    return num_correct / 3000 # just for now


def precision(query_obj: str,
           retrieved: List[str]):
    # This is the precision metric
    for cat in GARMENT_CATEGORIES:
        if cat in query_obj:
            query_label = cat

    retrieved_labels = infer_class(retrieved)
    # Find the number of correct items that correspond to the query.
    # As a correct item, we define the retrieved item that belongs to the
    # same class as the query object.
    num_correct = len(list(filter(lambda x: x == query_label, retrieved_labels)))
    # Return the recall metric defined as: num_correct / num_retrieved
    return num_correct / len(retrieved)


def run_eval(base_dir: Union[str, Path],
             cluster_centers_filename: Union[str, Path],
             global_descriptors_filename: Union[str, Path],
             data_path: Union[str, Path], # May be redundant, will keep it for now
             n_retrieved: int = 5,
             voxel_size: float = 12.0,
             hist_size: int = 256):
    dataset = mnq.retrieval3d.dataset.OBJDataset(base_dir=base_dir)

    # recalls = []
    precisions = {1: [],
                  2: [],
                  5: [],
                  10: [],
                  20: [],
                  50: []}

    recalls = {1: [],
               2: [],
               5: [],
               10: [],
               20: [],
               50: []}
    np.random.seed(12834)
    indices = np.random.permutation(len(dataset))
    validation_length = int(0.2 * len(dataset))

    # for query in dataset[indices[:validation_length]]:
    for index in indices[:validation_length]:
        query = dataset[index]
        for n_to_retrieve in recalls.keys():
            print(f'Running inference for input: {osp.basename(query)}\n# of retrieved items: {n_to_retrieve}')
            retrieved = mnq.retrieval3d.r3d.infer(input_filename=query,
                                                  cluster_centers_filename=cluster_centers_filename,
                                                  global_descriptors_filename=global_descriptors_filename,
                                                  n_retrieved=n_to_retrieve,
                                                  voxel_size=voxel_size,
                                                  hist_size=hist_size,
                                                  data_path=data_path)
            # recalls.append(recall(query_obj=query, retrieved=retrieved))
            recalls[n_to_retrieve].append(recall(query_obj=query, retrieved=retrieved))

    # recalls = np.asarray(recalls)
    for k, v in recalls.items():
        recalls = np.asarray(v)
        print(f'Precision@{k}: {np.mean(recalls):.4f}')
    # print(f'Recall@{n_retrieved}: {np.mean(recalls):.4f}')


if __name__ == '__main__':
    import os.path as osp
    home = os.getenv('HOME')
    run_eval(base_dir='/home/kaseris/Documents/3DGarments',
             cluster_centers_filename='/home/kaseris/Documents/dev/mannequin/data/r3d/clusters/cluster_centers_256.csv',
             global_descriptors_filename='/home/kaseris/Documents/dev/mannequin/data/r3d/descriptors/global_descriptors_256.csv',
             n_retrieved=1,
             data_path='/home/kaseris/Documents/3DGarments')