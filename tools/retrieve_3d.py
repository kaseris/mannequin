import argparse
import os
import os.path as osp
import re
import shutil

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


def save_image_result(query_name, retrieved_paths):
    """Saves the 3D pre-rendered images of the retrieved objects."""
    current_dir = os.getcwd()  # Find the directory where the function is called
    # /path/to/dataset/[category]/[object_name]/[object_name.obj] -> object_name
    dirname = osp.dirname(query_name)
    object_name = dirname.split('/')[-1]

    _path_to_save = osp.join(current_dir, object_name)
    if not osp.exists(_path_to_save):
        os.mkdir(_path_to_save)

    # Save the query image in the designated path
    for fname in os.listdir(dirname):
        if 'camera_front' in fname:
            _img_name = fname

    shutil.copy(osp.join(dirname, _img_name), _path_to_save)

    for retrieved_path in retrieved_paths:
        _directory = osp.dirname(retrieved_path)

        for _fname in os.listdir(_directory):
            if 'camera_front' in _fname:
                copy_this = _fname
        shutil.copy(osp.join(_directory, copy_this), _path_to_save)


if __name__ == '__main__':
    config = get_config()
    print('Start')
    path_to_data = '/home/kaseris/Documents/3DGarments'
    retrieved = infer(input_filename=config.in_file,
                      cluster_centers_filename=config.clusters_filename,
                      global_descriptors_filename=config.global_descriptors_file,
                      n_retrieved=config.n_retrieved,
                      voxel_size=config.voxel_size,
                      data_path=path_to_data,
                      hist_size=config.hist_size)
    save_image_result(config.in_file, retrieved)
