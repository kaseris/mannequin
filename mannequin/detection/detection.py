import numpy as np
import scipy.spatial.distance as distance


ANGLE_LARGE = 175.0
ANGLE_SMALL = 15.0


def detect_keypoints(coords: np.ndarray) -> np.ndarray:
    key_points = []
    for idx, point in enumerate(coords[1:-1]):
        current_point = point
        previous_point = coords[idx]
        next_point = coords[idx + 2]
        # The vector difference left to the current point
        l = current_point - previous_point
        # The vector difference right to the current point
        r = next_point - current_point
        # Calculate the dot product between the l and r vectors
        # in order to check the change in angle. We also record
        # where the dot product becomes zero or close to zero.
        # This would indicate a key point (supposedly).
        l_ = np.linalg.norm(l, ord=2)
        r_ = np.linalg.norm(r, ord=2)
        cos_theta = np.dot(l / l_, r / r_)
        theta = np.arccos(cos_theta)
        theta_deg = np.rad2deg(theta)
        if ANGLE_LARGE >= theta_deg >= ANGLE_SMALL:
            key_points.append(current_point)

    current_point = coords[0]
    previous_point = coords[-2]
    next_point = coords[1]

    l = current_point - previous_point
    r = next_point - current_point
    l_ = np.linalg.norm(l, ord=2)
    r_ = np.linalg.norm(r, ord=2)
    cos_theta = np.dot(l / l_, r / r_)
    theta = np.arccos(cos_theta)
    theta_deg = np.rad2deg(theta)
    if ANGLE_LARGE >= theta_deg >= ANGLE_SMALL:
        key_points.append(current_point)

    key_points = np.asarray(key_points)
    return key_points


def reject_outliers(reference_kp: np.ndarray,
                    input_kp: np.ndarray) -> np.ndarray:
    distance_mat = distance.cdist(input_kp, reference_kp)
    minimum_distance = np.min(distance_mat, axis=1)

    num_key_points_ref = len(reference_kp)
    num_key_points_inp = len(input_kp)

    num_outliers = num_key_points_inp - num_key_points_ref
    if num_outliers > 0:
        new_keypoints_input = np.argsort(minimum_distance)[:-num_outliers]
        key_points_input_refined = input_kp[new_keypoints_input]
        return key_points_input_refined
    else:
        return input_kp


def registration(reference_pattern: np.ndarray,
                 input_pattern: np.ndarray,
                 reference_kp: np.ndarray):

    max_ref_x, min_ref_x = np.max(reference_pattern[:, 0]), np.min(reference_pattern[:, 0])
    max_ref_y, min_ref_y = np.max(reference_pattern[:, 1]), np.min(reference_pattern[:, 1])

    reference_pattern[:, 0] -= (np.min(reference_pattern[:, 0]) + np.max(reference_pattern[:, 0])) / 2.
    reference_pattern[:, 1] -= (np.min(reference_pattern[:, 1]) + np.max(reference_pattern[:, 1])) / 2.
    input_pattern[:, 0] -= (np.min(input_pattern[:, 0]) + np.max(input_pattern[:, 0])) / 2.
    input_pattern[:, 1] -= (np.min(input_pattern[:, 1]) + np.max(input_pattern[:, 1])) / 2.

    reference_kp[:, 0] -= (max_ref_x + min_ref_x) / 2.
    reference_kp[:, 1] -= (max_ref_y + min_ref_y) / 2.

    # reference_kp[:, 0] -= (np.min(reference_pattern[:, 0]) + np.max(reference_pattern[:, 0])) / 2.
    # reference_kp[:, 1] -= (np.min(reference_pattern[:, 1]) + np.max(reference_pattern[:, 1])) / 2.

    return reference_pattern, input_pattern, reference_kp
