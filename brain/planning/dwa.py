"""
Dynamic Window Approach (DWA) — Real-time local obstacle avoidance.

Instead of blindly following the global path, DWA evaluates many possible
velocity commands and picks the one that best balances:
  1. Heading toward the goal
  2. Keeping distance from obstacles
  3. Moving fast

Algorithm:
1. Define a "dynamic window" of achievable velocities given current velocity + acceleration limits
2. Sample many (v, w) pairs from this window
3. For each pair, simulate a short trajectory (1-2 seconds)
4. Score each trajectory on goal heading, obstacle clearance, and speed
5. Pick the highest scoring trajectory
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    MAX_LINEAR_VEL, MAX_ANGULAR_VEL, MAX_LINEAR_ACC, MAX_ANGULAR_ACC,
    DWA_DT, DWA_PREDICT_TIME, DWA_V_SAMPLES, DWA_W_SAMPLES,
    DWA_GOAL_WEIGHT, DWA_OBSTACLE_WEIGHT, DWA_SPEED_WEIGHT,
    DWA_MIN_OBSTACLE_DIST, LIDAR_MAX_RANGE,
)


def dwa_control(pose, velocity, goal, obstacle_points):
    """
    Compute the best velocity command using DWA.

    Args:
        pose: [x, y, theta] — current robot pose
        velocity: [v, w] — current linear and angular velocity
        goal: (x, y) — target position in world coordinates
        obstacle_points: [(x, y), ...] — nearby obstacle positions in world coordinates

    Returns:
        best_v: Best linear velocity (m/s)
        best_w: Best angular velocity (rad/s)
        best_trajectory: List of (x, y, theta) for the best trajectory
    """
    x, y, theta = pose
    v_current, w_current = velocity

    # Dynamic window — reachable velocities in one timestep
    v_min = max(0.0, v_current - MAX_LINEAR_ACC * DWA_DT)
    v_max = min(MAX_LINEAR_VEL, v_current + MAX_LINEAR_ACC * DWA_DT)
    w_min = max(-MAX_ANGULAR_VEL, w_current - MAX_ANGULAR_ACC * DWA_DT)
    w_max = min(MAX_ANGULAR_VEL, w_current + MAX_ANGULAR_ACC * DWA_DT)

    best_score = -float('inf')
    best_v = 0.0
    best_w = 0.0
    best_traj = []

    # Sample velocities
    v_step = (v_max - v_min) / max(DWA_V_SAMPLES - 1, 1)
    w_step = (w_max - w_min) / max(DWA_W_SAMPLES - 1, 1)

    for vi in range(DWA_V_SAMPLES):
        v = v_min + vi * v_step

        for wi in range(DWA_W_SAMPLES):
            w = w_min + wi * w_step

            # Simulate trajectory
            traj = _simulate_trajectory(x, y, theta, v, w)

            # Score the trajectory
            score = _score_trajectory(traj, goal, obstacle_points, v)

            if score > best_score:
                best_score = score
                best_v = v
                best_w = w
                best_traj = traj

    return best_v, best_w, best_traj


def _simulate_trajectory(x, y, theta, v, w):
    """Simulate a trajectory for DWA_PREDICT_TIME seconds."""
    trajectory = [(x, y, theta)]
    steps = int(DWA_PREDICT_TIME / DWA_DT)

    for _ in range(steps):
        theta += w * DWA_DT
        x += v * math.cos(theta) * DWA_DT
        y += v * math.sin(theta) * DWA_DT
        trajectory.append((x, y, theta))

    return trajectory


def _score_trajectory(trajectory, goal, obstacle_points, v):
    """
    Score a trajectory based on three criteria:
    1. Heading: How well does the final heading point toward the goal?
    2. Obstacle clearance: Minimum distance to any obstacle
    3. Speed: Prefer faster trajectories
    """
    if not trajectory:
        return -float('inf')

    end_x, end_y, end_theta = trajectory[-1]

    # 1. Goal heading score — angle between trajectory endpoint heading and goal direction
    goal_angle = math.atan2(goal[1] - end_y, goal[0] - end_x)
    angle_diff = abs(math.atan2(math.sin(goal_angle - end_theta), math.cos(goal_angle - end_theta)))
    heading_score = math.pi - angle_diff  # higher = better aligned

    # 2. Obstacle clearance score — minimum distance to any obstacle along trajectory
    min_dist = float('inf')
    for tx, ty, _ in trajectory:
        for ox, oy in obstacle_points:
            d = math.sqrt((tx - ox) ** 2 + (ty - oy) ** 2)
            if d < min_dist:
                min_dist = d

    if min_dist < DWA_MIN_OBSTACLE_DIST:
        return -float('inf')  # Collision — reject this trajectory

    obstacle_score = min(min_dist, LIDAR_MAX_RANGE)  # cap

    # 3. Speed score — prefer moving forward
    speed_score = v

    # Weighted sum
    score = (DWA_GOAL_WEIGHT * heading_score +
             DWA_OBSTACLE_WEIGHT * obstacle_score +
             DWA_SPEED_WEIGHT * speed_score)

    return score


def lidar_to_obstacles(robot_x, robot_y, robot_theta, ranges, max_range=LIDAR_MAX_RANGE):
    """
    Convert LiDAR ranges to obstacle points in world coordinates.
    Only includes points that are actual obstacles (not max range readings).
    """
    obstacles = []
    num_rays = len(ranges)
    angle_inc = 2 * math.pi / num_rays

    for i, r in enumerate(ranges):
        if r > 0.05 and r < max_range * 0.95:  # actual obstacle, not max range
            angle = robot_theta + i * angle_inc
            ox = robot_x + r * math.cos(angle)
            oy = robot_y + r * math.sin(angle)
            obstacles.append((ox, oy))

    return obstacles
