import sys
import time

import matplotlib.pyplot as plt
import numpy as np

from detection import detect_keypoints, registration, reject_outliers
from fileio import read_coords_from_txt
from misc import plot_matching_with_annos, normalize
from primitives.utils import create_sides_dict, create_panel_dict, rearrange_keypoints
from primitives import Panel
from shape_context import ShapeContext
from TPS import TPS_generate, TPS_grid, TPS_project

show = True if int(sys.argv[1]) else False


def main():
    reference_panel = read_coords_from_txt('Q9020front-S_38.xyz', delimiter=',')
    input_panel = read_coords_from_txt('Q5134front-S_M.xyz', delimiter=',')

    reference_kp = np.array([[1242.60922196, 251.7639571],
                             [1220.10922196, 648.9019571],
                             [1180.76922196, 846.5749571],
                             [1080.10422196, 886.7329571],
                             [875.16722196, 886.7329571],
                             [774.50222196, 846.5749571],
                             [735.16222196, 648.9019571],
                             [712.66222196, 251.7639571]])

    reference_reg, input_reg, reference_kp_reg = registration(reference_pattern=reference_panel,
                                                              input_pattern=input_panel,
                                                              reference_kp=reference_kp)
    plt.rcParams['figure.figsize'] = (8, 10)
    plt.gca().set_aspect('equal')
    if show:
        plt.scatter(reference_reg[:, 0], reference_reg[:, 1])
        plt.scatter(input_reg[:, 0], input_reg[:, 1])
        plt.title('Patterns after registration')
        plt.legend(['Reference pattern', 'Input pattern'])
        plt.show()

    candidate_kp = detect_keypoints(coords=input_reg)

    if show:
        plt.scatter(reference_reg[:, 0], reference_reg[:, 1])
        plt.scatter(input_reg[:, 0], input_reg[:, 1])
        plt.scatter(candidate_kp[:, 0], candidate_kp[:, 1], s=80)
        plt.title('Detected keypoints after early detection')
        plt.legend(['reference pattern', 'input pattern', 'key points'])
        plt.show()

    refined_kp = reject_outliers(reference_kp=reference_kp_reg,
                                 input_kp=candidate_kp)
    if show:
        plt.scatter(reference_reg[:, 0], reference_reg[:, 1])
        plt.scatter(input_reg[:, 0], input_reg[:, 1])
        plt.scatter(refined_kp[:, 0], refined_kp[:, 1], s=80)
        plt.scatter(reference_kp_reg[:, 0], reference_kp_reg[:, 1], s=80)
        plt.title('Detected keypoints after outlier rejection')
        plt.legend(['reference pattern', 'input pattern', 'key points', 'reference pattern keypoints'])
        plt.show()

    refined_kp = rearrange_keypoints(kp=refined_kp)
    sides = create_sides_dict(kp=refined_kp, pattern_array=input_reg)
    panel_properties = create_panel_dict(sides=sides, panel_name='front')

    panel = Panel(**panel_properties)

    sides_ref = create_sides_dict(kp=reference_kp_reg, pattern_array=reference_reg)
    ref_panel_properties = create_panel_dict(sides=sides_ref, panel_name='front')

    panel_ref = Panel(**ref_panel_properties)
    if show:
        plt.scatter(panel_ref.point_cloud[:, 0], panel.point_cloud[:, 1])
        plt.scatter(panel.point_cloud[:, 0], panel.point_cloud[:, 1])
        plt.title('Parametric panel of the input and reference patterns after keypoint detection')
        plt.legend(['reference pattern', 'input pattern'])
        plt.show()

    sc = ShapeContext()

    P = sc.compute(panel_ref.point_cloud)
    Q = sc.compute(panel.point_cloud)

    cost, indices = sc.diff(P=P, Q=Q)

    lines = []
    lines_correct = []
    lines_incorrect = []
    matches = dict()
    matches['src'] = []
    matches['matches'] = []
    for p1, q1 in indices:
        if p1 == q1:
            lines_correct.append([[panel_ref.point_cloud[p1][0], panel_ref.point_cloud[p1][1]],
                                  [panel.point_cloud[q1][0], panel.point_cloud[q1][1]]])
        else:
            lines_incorrect.append([[panel_ref.point_cloud[p1][0], panel_ref.point_cloud[p1][1]],
                                    [panel.point_cloud[q1][0], panel.point_cloud[q1][1]]])

        matches['src'].append(panel_ref.point_cloud[p1])
        matches['matches'].append(panel.point_cloud[q1])
        lines.append([[panel_ref.point_cloud[p1][0], panel_ref.point_cloud[p1][1]],
                      [panel.point_cloud[q1][0], panel.point_cloud[q1][1]]])

    plot_matching_with_annos(panel_ref.point_cloud,
                             panel.point_cloud,
                             lines_cor=lines_correct,
                             lines_inc=lines_incorrect)

    ref_norm = normalize(np.asarray(matches['src']))
    inp_norm = normalize(np.asarray(matches['matches']))
    ref_norm = ref_norm[::2]
    inp_norm = inp_norm[::2]

    st_tps_gen = time.time()
    g = TPS_generate(ref_norm, inp_norm)
    print(f'Bending energy: {g["be"]:.3f}')
    print(f'Profile TPS: {time.time() - st_tps_gen:.3f} sec.')

    if show:
        grid = TPS_grid(
            g=g,
            maxx=1.0,
            minx=0.0,
            maxy=1.0,
            miny=0.0,
            major_step=0.1,
            minor_step=0.01,
            res=2000
        )

        grid.show()


if __name__ == '__main__':
    main()
