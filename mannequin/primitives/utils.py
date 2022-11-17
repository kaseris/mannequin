import numpy as np

from mannequin.fileio.fileio import *
from mannequin.lerp.splines import fit_bezier


def read_keypoints(seam_structure: dict,
                   panel_side: str = 'front'):
    """Infers a garment's keypoints """
    # Get the connections of the front pattern to the back
    connections = seam_structure[panel_side]['connections']
    indices = []
    for idx, conn in enumerate(connections):
        if 'back' in conn:
            indices.append(idx)

    if len(indices) == 2:
        for idx, conn in enumerate(connections):
            if 'sleeve' in conn:
                indices.append(idx)

    # Find the seam points of the pattern A to the pattern B
    seams = []
    for idx in indices:
        seams.append(seam_structure[panel_side]['seams'][idx])

    starting_points = []
    end_points = []

    for seam in seams:
        starting_points.append((float(seam[0]), float(seam[1])))
        end_points.append((float(seam[-2]), float(seam[-1])))

    return np.array(starting_points + end_points)


def sort_xy(arr: np.ndarray):
    """Sort a set of coordinates in a counter-clockwise manner.
    """
    x, y = arr[:, 0], arr[:, 1]

    x0 = np.mean(x)
    y0 = np.mean(y)

    r = np.sqrt((x - x0) ** 2 + (y - y0) ** 2)

    angles = np.where((y - y0) > 0, np.arccos((x - x0) / r), 2 * np.pi - np.arccos((x - x0) / r))

    mask = np.argsort(angles)

    x_sorted = x[mask]
    y_sorted = y[mask]

    return np.column_stack((x_sorted, y_sorted))


def rearrange_keypoints(kp: np.ndarray):
    # Sort the keypoints array indices in a ccw manner
    sorted_by_angle = sort_xy(kp[:, 0], kp[:, 1])

    # Find the lowest point by y then find the max X
    idx_sorted_by_y = np.argsort(sorted_by_angle[:, 1])[:2]
    lowest_points = sorted_by_angle[idx_sorted_by_y]
    where_max_X = np.argmax(lowest_points[:, 0])

    # Find the index of the lower-right point in the keypoints array
    # We store it in the idx_key_point_start var
    coords_key_point_start = lowest_points[where_max_X]
    idx_key_point_start = np.where(np.all(sorted_by_angle == coords_key_point_start,
                                          axis=1))[0][0]

    # Re-arrange the key_points matrix so that it starts from the
    # bottom right point
    if idx_key_point_start != 0:
        sorted_by_angle = np.vstack((sorted_by_angle[idx_key_point_start:, :],
                                     sorted_by_angle[:idx_key_point_start, :]))

    # Remove possible duplicate entries
    key_point_indices = np.unique(sorted_by_angle, axis=0, return_index=True)[1]
    key_points = np.asarray([sorted_by_angle[index] for index in sorted(key_point_indices)])
    return key_points


def create_sides_dict(kp: np.ndarray,
                      pattern_array: np.ndarray):
    """

    :param kp: The keypoints of the panel.
    :param pattern_array: The panel read from the .xyz file
    :return:
    """
    # Determine the direction in which the keypoints are scattered on the plane.
    # Can be CW/CCW
    # TODO: Explain how the direction is inferred.
    start_ = np.where(np.all(kp[0] == pattern_array, axis=1))[0][0]


    pattern_array = np.vstack((pattern_array[start_:], pattern_array[:start_]))
    pattern_array = np.vstack((pattern_array, pattern_array[0, :]))

    second_key_point = np.where(np.all(kp[1] == pattern_array, axis=1))[0][0]
    final_key_point = np.where(np.all(kp[-1] == pattern_array, axis=1))[0][0]

    if second_key_point > final_key_point:
        pattern_array = np.flip(pattern_array, 0)

    # Create the sides dictionary
    if kp.shape[0] == 8:
        sides = dict()
        side_types = ['side1', 'sleeve1', 'shoulder1',
                      'collar', 'shoulder2', 'sleeve2', 'side2',
                      'belt']
    elif kp.shape[0] == 10:
        sides = dict()
        side_types = ['side1', 'sleeve1', 'shoulder1a', 'shoulder1b',
                      'collar', 'shoulder2a', 'shoulder2b', 'sleeve2', 'side2',
                      'belt']
    elif kp.shape[0] == 6:
        sides = dict()
        side_types = ['side1', 'sleeve1', 'collar',
                      'sleeve2', 'side2', 'belt']
    else:
        raise ValueError('Error')

    old = 0
    for i, key_point in enumerate(kp[1:]):
        idx = np.where(np.all(key_point == pattern_array, axis=1))[0][0]
        # print(idx, key_point)
        sides[i] = dict(region=pattern_array[old:idx + 1],
                        side_type=side_types[i])
        old = idx

    sides[len(kp) - 1] = dict(region=pattern_array[old:len(pattern_array)],
                              side_type=side_types[-1])
    return sides


def create_panel_dict(sides: dict,
                      panel_name: str = 'front') -> dict:
    for key in sides.keys():

        region = sides[key].get('region')

        # Fit a bezier curve given the region
        if len(region) in [2, 3, 4]:
            # Ignore fitting a bezier curve onto a region that consists of 2, 3 or 4 points.
            # To model it, we simply fit a 2-control point bezier curve, which results to
            # a straight line.
            control_points = fit_bezier(region, 1)
        else:
            control_points = fit_bezier(region, 5)

        control_points[0] = sides[key].get('region')[0]
        control_points[-1] = sides[key].get('region')[-1]
        sides[key]['bezier'] = control_points

    properties = dict()
    properties['name'] = panel_name
    for i in range(len(sides)):
        properties[f'edge{str(i)}'] = dict(type='bez',
                                           control_points=sides[i]['bezier'])
    return properties


if __name__ == '__main__':
    pattern_array = read_coords_from_txt('../Q9020front-S_38.xyz', delimiter=',')
    keypoints = np.array(([[1242.60922196, 251.7639571],
                           [1220.10922196, 648.9019571],
                           [1180.76922196, 846.5749571],
                           [1080.10422196, 886.7329571],
                           [875.16722196, 886.7329571],
                           [774.50222196, 846.5749571],
                           [735.16222196, 648.9019571],
                           [712.66222196, 251.7639571]]))

    sides = create_sides_dict(kp=keypoints, pattern_array=pattern_array)
    panel_dict = create_panel_dict(sides=sides, panel_name='front')
    # from primitives import Panel
    # panel = Panel(**panel_dict)
    #
    # import matplotlib.pyplot as plt
    #
    # plt.scatter(panel.point_cloud[:, 0], panel.point_cloud[:, 1])
    # plt.show()
