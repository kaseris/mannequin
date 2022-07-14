from mannequin.retrieval3d.r3d import infer, visualize_point_cloud

if __name__ == '__main__':
    retrieved = retrieved = infer(
        '/home/kaseris/Documents/3DGarments/dress_sleeveless_2550/dress_sleeveless_WQH14U9OKF/dress_sleeveless_WQH14U9OKF_sim.obj',
        cluster_centers_filename='/home/kaseris/Documents/dev/mannequin/data/r3d/clusters/cluster_centers_256.csv',
        global_descriptors_filename='/home/kaseris/Documents/dev/mannequin/data/r3d/descriptors/global_descriptors_256.csv',
        hist_size=256)
