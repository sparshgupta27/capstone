"""
Frontier Explorer — Autonomous exploration by finding unexplored regions.

A frontier is the boundary between known-free space and unknown space.
The robot explores by repeatedly navigating to the nearest/largest frontier.

Algorithm:
1. Scan the occupancy grid for frontier cells (free cells adjacent to unknown cells)
2. Cluster adjacent frontier cells into frontier groups
3. Score each group by size × distance
4. Pick the best frontier as the next exploration target
"""
import math
from collections import deque
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import FRONTIER_MIN_SIZE, FRONTIER_DISTANCE_WEIGHT, FRONTIER_SIZE_WEIGHT


def find_frontiers(occupancy_grid, robot_gx, robot_gy):
    """
    Find all frontier cells in the occupancy grid.

    A frontier cell is a FREE cell that is adjacent to at least one UNKNOWN cell.

    Args:
        occupancy_grid: OccupancyGrid object
        robot_gx, robot_gy: Robot position in grid coordinates

    Returns:
        List of frontier clusters, each cluster is a list of (gx, gy) cells
    """
    grid = occupancy_grid
    w, h = grid.width, grid.height

    # Step 1: Find all frontier cells
    frontier_cells = set()
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for gy in range(h):
        for gx in range(w):
            if not grid.is_free(gx, gy):
                continue

            # Check if any neighbor is unknown
            for dx, dy in neighbors:
                nx, ny = gx + dx, gy + dy
                if grid.is_unknown(nx, ny):
                    frontier_cells.add((gx, gy))
                    break

    if not frontier_cells:
        return []

    # Step 2: Cluster frontier cells using BFS flood fill
    visited = set()
    clusters = []

    for cell in frontier_cells:
        if cell in visited:
            continue

        # BFS to find connected frontier cells
        cluster = []
        queue = deque([cell])
        visited.add(cell)

        while queue:
            cx, cy = queue.popleft()
            cluster.append((cx, cy))

            for dx, dy in neighbors + [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                nx, ny = cx + dx, cy + dy
                neighbor = (nx, ny)
                if neighbor in frontier_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if len(cluster) >= FRONTIER_MIN_SIZE:
            clusters.append(cluster)

    return clusters


def score_frontier(cluster, robot_gx, robot_gy):
    """
    Score a frontier cluster based on size and distance.
    Higher score = more attractive target.
    """
    # Centroid of the cluster
    cx = sum(c[0] for c in cluster) / len(cluster)
    cy = sum(c[1] for c in cluster) / len(cluster)

    # Distance from robot
    dist = math.sqrt((cx - robot_gx) ** 2 + (cy - robot_gy) ** 2)
    if dist < 1:
        dist = 1  # avoid division issues

    # Score: prefer large, close frontiers
    size_score = len(cluster) * FRONTIER_SIZE_WEIGHT
    distance_penalty = dist * FRONTIER_DISTANCE_WEIGHT

    return size_score / distance_penalty


def select_best_frontier(occupancy_grid, robot_x, robot_y):
    """
    Find the best frontier to explore next.

    Args:
        occupancy_grid: OccupancyGrid object
        robot_x, robot_y: Robot position in world coordinates

    Returns:
        target: (world_x, world_y) — centroid of the best frontier, or None if fully explored
    """
    robot_gx, robot_gy = occupancy_grid.world_to_grid(robot_x, robot_y)

    clusters = find_frontiers(occupancy_grid, robot_gx, robot_gy)

    if not clusters:
        return None  # Fully explored!

    # Score and rank
    best_score = -float('inf')
    best_cluster = None

    for cluster in clusters:
        score = score_frontier(cluster, robot_gx, robot_gy)
        if score > best_score:
            best_score = score
            best_cluster = cluster

    if best_cluster is None:
        return None

    # Return centroid of best cluster in world coordinates
    cx = sum(c[0] for c in best_cluster) / len(best_cluster)
    cy = sum(c[1] for c in best_cluster) / len(best_cluster)

    return occupancy_grid.grid_to_world(int(cx), int(cy))
