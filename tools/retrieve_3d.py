import argparse
import os
import os.path as osp

import mannequin as mnq

from mannequin.retrieval3d.r3d import infer, visualize_point_cloud


def get_config():
    parser = argparse.ArgumentParser(description='3D Retrieval inference tool.')

    parser.add_argument('-i', '--in_file', type=str, help='Input filename.', required=True)
    parser.add_argument('--clusters_filename', type=str,
                        default=osp.join(mnq.MNQ_3DPC_DATASET_CLUSTERS_DIR,
                                         'cluster_centers_256.csv'),
                        help='Path to the filename that stores the FPFH word dictionary (cluster centers).')
    parser.add_argument('--global_descriptors_file', type=str,
                        default=osp.join(mnq.MNQ_3DPC_DATASET_GLOBAL_DESCRIPTORS,
                                         'global_descriptors_256.csv'),
                        help='Path to the file that stores the global descriptors of our OBJ dataset.')
    parser.add_argument('--n_retrieved', type=int, default=5, help='Number of items to retrieve.')
    parser.add_argument('--voxel_size', type=float, default=12.0,
                        help='Downsampling rate. Higher value means more downsampling')
    parser.add_argument('--hist_size', type=int, default=256, help='Histogram size.')

    return parser.parse_args()


if __name__ == '__main__':
    config = get_config()

    retrieved = infer(input_filename=config.in_file,
                      cluster_centers_filename=config.clusters_filename,
                      global_descriptors_filename=config.global_descriptors_file,
                      n_retrieved=config.n_retrieved,
                      voxel_size=config.voxel_size,
                      hist_size=config.hist_size)
