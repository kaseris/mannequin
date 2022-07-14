from mannequin.retrieval3d.r3d import infer


def test_inference_output():
    sample = '/home/kaseris/Documents/3DGarments/dress_sleeveless_2550/dress_sleeveless_WQH14U9OKF/dress_sleeveless_WQH14U9OKF_sim.obj'
    retrieved = infer(input_filename=sample,
                      cluster_centers_filename='/home/kaseris/Documents/dev/mannequin/data/r3d/clusters/cluster_centers_256.csv',
                      global_descriptors_filename='/home/kaseris/Documents/dev/mannequin/data/r3d/descriptors/global_descriptors_256.csv',
                      hist_size=256)
    assert not not retrieved
