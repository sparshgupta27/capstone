"""
ICP Scan Matcher — Iterative Closest Point algorithm for aligning consecutive LiDAR scans.

Given two sets of 2D points (previous scan and current scan), ICP finds the
rotation and translation that best aligns them. This tells us how much the
robot moved between scans — more accurate than wheel odometry alone.

Algorithm:
1. For each point in the current scan, find the closest point in the previous scan
2. Compute the optimal rotation + translation to minimize the distance between matched pairs
3. Apply the transform to the current scan
4. Repeat until convergence
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import ICP_MAX_ITERATIONS, ICP_TOLERANCE, ICP_MAX_CORRESPONDENCE_DIST


def polar_to_cartesian(ranges, angle_min, angle_increment, max_range):
    """Convert polar LiDAR scan to 2D cartesian points."""
    points = []
    for i, r in enumerate(ranges):
        if r > 0.05 and r < max_range:
            angle = angle_min + i * angle_increment
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            points.append((x, y))
    return points


def transform_points(points, dx, dy, dtheta):
    """Apply a rigid body transform (rotation + translation) to a set of points."""
    cos_t = math.cos(dtheta)
    sin_t = math.sin(dtheta)
    result = []
    for px, py in points:
        nx = cos_t * px - sin_t * py + dx
        ny = sin_t * px + cos_t * py + dy
        result.append((nx, ny))
    return result


def find_closest(point, reference_points):
    """Find the closest point in the reference set. Returns (closest_point, distance)."""
    min_dist = float('inf')
    closest = None
    px, py = point
    for rx, ry in reference_points:
        d = (px - rx) ** 2 + (py - ry) ** 2
        if d < min_dist:
            min_dist = d
            closest = (rx, ry)
    return closest, math.sqrt(min_dist)


def compute_centroid(points):
    """Compute the centroid of a set of 2D points."""
    if not points:
        return (0.0, 0.0)
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return (cx, cy)


def icp_match(source_points, target_points, max_iter=ICP_MAX_ITERATIONS,
              tolerance=ICP_TOLERANCE, max_dist=ICP_MAX_CORRESPONDENCE_DIST):
    """
    ICP scan matching — find the transform that aligns source to target.

    Args:
        source_points: Current scan points [(x, y), ...] in robot frame
        target_points: Previous scan points [(x, y), ...] in robot frame
        max_iter: Maximum iterations
        tolerance: Convergence threshold
        max_dist: Maximum correspondence distance

    Returns:
        (dx, dy, dtheta): The estimated rigid body transform
        error: Final mean squared error
    """
    if len(source_points) < 10 or len(target_points) < 10:
        return (0.0, 0.0, 0.0), float('inf')

    # Work with copies
    current = list(source_points)
    total_dx, total_dy, total_dtheta = 0.0, 0.0, 0.0
    prev_error = float('inf')

    for iteration in range(max_iter):
        # Step 1: Find correspondences
        matched_src = []
        matched_tgt = []

        for sp in current:
            closest, dist = find_closest(sp, target_points)
            if dist < max_dist:
                matched_src.append(sp)
                matched_tgt.append(closest)

        if len(matched_src) < 5:
            break

        # Step 2: Compute centroids
        src_centroid = compute_centroid(matched_src)
        tgt_centroid = compute_centroid(matched_tgt)

        # Step 3: Compute optimal rotation using SVD-like approach
        # For 2D, we can compute this analytically without numpy
        numerator = 0.0
        denominator = 0.0

        for (sx, sy), (tx, ty) in zip(matched_src, matched_tgt):
            # Centered coordinates
            sxc = sx - src_centroid[0]
            syc = sy - src_centroid[1]
            txc = tx - tgt_centroid[0]
            tyc = ty - tgt_centroid[1]

            numerator += sxc * tyc - syc * txc
            denominator += sxc * txc + syc * tyc

        dtheta = math.atan2(numerator, denominator)

        # Step 4: Compute translation
        cos_t = math.cos(dtheta)
        sin_t = math.sin(dtheta)
        dx = tgt_centroid[0] - (cos_t * src_centroid[0] - sin_t * src_centroid[1])
        dy = tgt_centroid[1] - (sin_t * src_centroid[0] + cos_t * src_centroid[1])

        # Step 5: Apply transform
        current = transform_points(current, dx, dy, dtheta)
        total_dx += dx
        total_dy += dy
        total_dtheta += dtheta

        # Compute error
        error = 0.0
        for sp, tp in zip(matched_src, matched_tgt):
            error += (sp[0] - tp[0]) ** 2 + (sp[1] - tp[1]) ** 2
        error /= len(matched_src)

        # Check convergence
        if abs(prev_error - error) < tolerance:
            break
        prev_error = error

    return (total_dx, total_dy, total_dtheta), prev_error
