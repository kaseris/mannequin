import os.path as osp
import time

import numpy as np
import open3d as o3d

from pathlib import Path
from typing import Union

from scipy.spatial.distance import cdist
from sklearn.cluster import MiniBatchKMeans

from mannequin.fileio import read_obj

import mannequin.retrieval3d


__all__ = ['generate_point_cloud', 'generate_point_cloud_object',
           'downsample_point_cloud', 'compute_fpfh', 'infer', 'train_bow']


def generate_point_cloud(filename: Union[str, Path]) -> np.ndarray:
    r"""Reads a Wavefront OBJ file and returns a NumPy array of the read point cloud."""
    return np.asarray(read_obj(filename))


def generate_point_cloud_object(point_cloud: np.ndarray) -> o3d.geometry.PointCloud:
    r"""Prepares a point cloud NumPy array in order to be in a processable form for Open3D."""
    verts_pc = o3d.geometry.PointCloud()
    verts_pc.points = o3d.utility.Vector3dVector(point_cloud)
    return verts_pc


def downsample_point_cloud(point_cloud: o3d.geometry.PointCloud,
                           voxel_size: float = 2.0
                           ) -> o3d.geometry.PointCloud:
    pcd_down = point_cloud.voxel_down_sample(voxel_size)
    return pcd_down


def compute_fpfh(point_cloud: o3d.geometry.PointCloud,
                 voxel_size=2.0,
                 max_nn_normal_estimation: int = 30,
                 max_nn_fpfh_estimation: int = 100) -> np.ndarray:
    r"""Computes the FPFH descriptor for a point cloud."""
    point_cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 2.0,
                                                                      max_nn=max_nn_normal_estimation))
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(point_cloud,
                                                           o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 5.0,
                                                                                                max_nn=max_nn_fpfh_estimation))
    return np.asarray(fpfh.data)


def train_bow(dataset_base_dir: Union[str, Path],
              batch_size: int = 16,
              num_clusters: int = 256):
    dataset = mannequin.retrieval3d.dataset.OBJDataset(base_dir=dataset_base_dir)
    data_loader = mannequin.retrieval3d.dataset.OBJDataLoader(dataset=dataset,
                                batch_size=batch_size)
    mini_batch_kmeans = MiniBatchKMeans(n_clusters=num_clusters,
                                        batch_size=1000)
    print('Starting MiniBatch K-Means...')
    st = time.monotonic()
    st_batch = time.monotonic()
    for idx, el in enumerate(data_loader):
        mini_batch_kmeans = mini_batch_kmeans.partial_fit(el[:1000, :])
        print(f'Batch: {idx + 1}, Element Shape: {el.shape}, Batch processing time: {time.monotonic() - st_batch:.3f}s')
        st_batch = time.monotonic()
    print(f'Finished training of the MiniBatch K-Means. Elapsed Time: {time.monotonic() - st:.3f}s')
    print('Saving clusters')
    np.savetxt('/home/kaseris/Documents/mannequin/cluster_centers_256.csv',
               mini_batch_kmeans.cluster_centers_,
               delimiter=',')


def find_cluster_indices(fpfh_features: np.ndarray,
                         cluster_centers: np.ndarray) -> np.ndarray:
    r"""For each FPFH feature, determine to which cluster centre the local descriptor belongs.
    The index returned is the argument that minimizes the distance between the FPFH local descriptor and
    the cluster centers (words).

        :param fpfh_features: A :math:`N \times 33` array of FPFH local descriptors
        :param cluster_centers: The word dictionary.

    """
    dists = cdist(fpfh_features, cluster_centers)
    return np.argmin(dists, axis=1)


def compute_histogram(indices: np.ndarray,
                      hist_size: int = 128,
                      normalize: bool = True) -> np.ndarray:
    """Calculates a global histogram descriptor from the words contained in a point cloud.
    """
    # Create the histogram
    hist = np.zeros(hist_size)
    # Increment by 1 at the bins that correspond to the word's closest centre.
    np.add.at(hist, indices, 1)
    if normalize:
        return hist / hist.sum()
    else:
        return hist


def visualize_point_cloud(input_filename: Union[str, Path]):
    pc = generate_point_cloud(input_filename)
    pc = generate_point_cloud_object(pc)
    o3d.visualization.draw(pc)


def infer(input_filename: Union[str, Path],
          cluster_centers_filename: Union[str, Path],
          global_descriptors_filename: Union[str, Path],
          n_retrieved: int = 5,
          voxel_size: float = 12.0,
          hist_size: int = 128):
    input_file = input_filename
    print(f'Running inference for input: {osp.basename(input_file)}')
    input_pc = generate_point_cloud(input_file)
    input_pc = generate_point_cloud_object(input_pc)
    input_pc = downsample_point_cloud(input_pc, voxel_size=voxel_size)
    # Load the cluster centers
    _cluster_centers = np.genfromtxt(cluster_centers_filename, delimiter=',')
    # Load the global descriptors database
    global_descriptors = np.genfromtxt(global_descriptors_filename, delimiter=',')

    # Calculate the point cloud's FPFH descriptor
    fpfh = compute_fpfh(input_pc).T
    # Generate a global descriptor for the input point cloud.
    _indices = find_cluster_indices(fpfh_features=fpfh, cluster_centers=_cluster_centers)
    _pc_histogram = compute_histogram(indices=_indices, hist_size=hist_size,
                                      normalize=True)

    # Find distances between the input's global descriptor and the database's entries
    dists = cdist(np.expand_dims(_pc_histogram, 1).T, global_descriptors)

    # Find the closest n_retrieved distances and return their indices.
    retrieved_indices = np.argsort(dists)[0][1:n_retrieved+1]

    # Create the dataset object in order to return the filenames
    _ds = mannequin.retrieval3d.dataset.OBJDataset(base_dir=mannequin.retrieval3d.dataset.DATASET_BASE_DIR)
    retrieved_paths = []
    for retrieved_index in retrieved_indices:
        print(_ds[retrieved_index])
        retrieved_paths.append(_ds[retrieved_index])
    return retrieved_paths


def extract_global_descriptors(dataset_dir: Union[str, Path],
                               cluster_centers_file: Union[str, Path],
                               batch_size: int = 1):
    dataset = mannequin.retrieval3d.dataset.OBJDataset(base_dir=mannequin.retrieval3d.dataset.DATASET_BASE_DIR)
    data_loader = mannequin.retrieval3d.dataset.OBJDataLoader(dataset=dataset,
                                                              batch_size=1)
    cluster_centers = np.genfromtxt(cluster_centers_file, delimiter=',')
    histograms = []
    print('Starting extracting global descriptors...')
    st = time.monotonic()
    for idx, el in enumerate(data_loader):
        print(f'Element: {idx + 1}\t Elapsed time: {time.monotonic() - st:.3f}s from start.', flush=True)
        # Find the cluster participation of the FPFH descriptors
        indices = find_cluster_indices(fpfh_features=el, cluster_centers=cluster_centers)
        # Describe the point cloud with a global histogram
        pc_histogram = compute_histogram(indices=indices, hist_size=256,
                                         normalize=True)
        histograms.append(pc_histogram)
    et = time.monotonic() - st
    print(f'Completed in {et:.3f}s.')
    print('Saving the global descriptors.....')
    histograms = np.vstack(histograms)
    np.savetxt('/home/kaseris/Documents/mannequin/global_descriptors_256.csv', histograms, delimiter=',')
    print('Done.')


if __name__ == '__main__':
    pass
