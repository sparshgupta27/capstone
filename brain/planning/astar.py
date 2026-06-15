"""
A* Path Planner — Finds the shortest collision-free path on the occupancy grid.

Features:
- 8-connected grid (diagonal moves allowed)
- Configurable heuristic weight for speed vs optimality tradeoff
- Works on inflated obstacle grid (robot won't clip walls)
- Path smoothing to reduce zig-zag patterns
"""
import math
import heapq
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import ASTAR_ALLOW_DIAGONAL, ASTAR_WEIGHT


# Movement directions: (dx, dy, cost)
MOVES_4 = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0)]
MOVES_8 = MOVES_4 + [
    (1, 1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (-1, -1, 1.414)
]


def heuristic(gx1, gy1, gx2, gy2):
    """Euclidean distance heuristic."""
    return math.sqrt((gx1 - gx2) ** 2 + (gy1 - gy2) ** 2)


def astar(grid, start, goal, allow_diagonal=ASTAR_ALLOW_DIAGONAL, weight=ASTAR_WEIGHT):
    """
    A* pathfinding on a 2D boolean grid.

    Args:
        grid: 2D list where True = blocked, False = passable (use inflated grid!)
        start: (gx, gy) start cell
        goal: (gx, gy) goal cell
        allow_diagonal: Allow 8-connected movement
        weight: Heuristic weight (1.0 = optimal, >1 = faster but suboptimal)

    Returns:
        path: List of (gx, gy) cells from start to goal, or empty list if no path
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    sx, sy = start
    gx, gy = goal

    # Bounds check
    if not (0 <= sx < width and 0 <= sy < height):
        return []
    if not (0 <= gx < width and 0 <= gy < height):
        return []

    # Check if start or goal is blocked
    if grid[sy][sx] or grid[gy][gx]:
        return []

    moves = MOVES_8 if allow_diagonal else MOVES_4

    # Priority queue: (f_score, g_score, x, y)
    open_set = [(0.0, 0.0, sx, sy)]
    came_from = {}
    g_score = {(sx, sy): 0.0}
    closed = set()

    while open_set:
        f, g, cx, cy = heapq.heappop(open_set)

        if (cx, cy) in closed:
            continue
        closed.add((cx, cy))

        # Goal reached
        if cx == gx and cy == gy:
            # Reconstruct path
            path = [(cx, cy)]
            while (cx, cy) in came_from:
                cx, cy = came_from[(cx, cy)]
                path.append((cx, cy))
            path.reverse()
            return path

        # Explore neighbors
        for dx, dy, cost in moves:
            nx, ny = cx + dx, cy + dy

            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if grid[ny][nx]:  # blocked
                continue
            if (nx, ny) in closed:
                continue

            # For diagonal moves, also check the two adjacent cells
            # to prevent corner-cutting through walls
            if dx != 0 and dy != 0:
                if grid[cy][cx + dx] or grid[cy + dy][cx]:
                    continue

            new_g = g + cost

            if new_g < g_score.get((nx, ny), float('inf')):
                g_score[(nx, ny)] = new_g
                f_score = new_g + weight * heuristic(nx, ny, gx, gy)
                came_from[(nx, ny)] = (cx, cy)
                heapq.heappush(open_set, (f_score, new_g, nx, ny))

    return []  # No path found


def smooth_path(path, grid, iterations=50):
    """
    Smooth a grid-based path to reduce zig-zagging.
    Uses gradient descent to pull path points toward a straight line
    while keeping them away from obstacles.
    """
    if len(path) <= 2:
        return path

    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # Convert to floats for smoothing
    smooth = [(float(x), float(y)) for x, y in path]
    weight_data = 0.5   # keep close to original
    weight_smooth = 0.3  # pull toward smooth line

    for _ in range(iterations):
        for i in range(1, len(smooth) - 1):
            ox, oy = float(path[i][0]), float(path[i][1])
            px, py = smooth[i]
            prev_x, prev_y = smooth[i - 1]
            next_x, next_y = smooth[i + 1]

            # Smoothing update
            new_x = px + weight_data * (ox - px) + weight_smooth * (prev_x + next_x - 2 * px)
            new_y = py + weight_data * (oy - py) + weight_smooth * (prev_y + next_y - 2 * py)

            # Check if new position is valid
            gx, gy = int(round(new_x)), int(round(new_y))
            if 0 <= gx < width and 0 <= gy < height and not grid[gy][gx]:
                smooth[i] = (new_x, new_y)

    return [(int(round(x)), int(round(y))) for x, y in smooth]


def plan_path(occupancy_grid, start_world, goal_world):
    """
    High-level path planning interface.

    Args:
        occupancy_grid: OccupancyGrid object
        start_world: (x, y) in world coordinates (meters)
        goal_world: (x, y) in world coordinates (meters)

    Returns:
        path_world: List of (x, y) waypoints in world coordinates, or empty list
    """
    # Get inflated grid for safe path planning
    inflated = occupancy_grid.get_inflated_grid()

    # Convert world to grid coordinates
    sx, sy = occupancy_grid.world_to_grid(start_world[0], start_world[1])
    gx, gy = occupancy_grid.world_to_grid(goal_world[0], goal_world[1])

    # Run A*
    path_grid = astar(inflated, (sx, sy), (gx, gy))

    if not path_grid:
        return []

    # Smooth the path
    path_grid = smooth_path(path_grid, inflated)

    # Convert back to world coordinates
    path_world = []
    for gx, gy in path_grid:
        wx, wy = occupancy_grid.grid_to_world(gx, gy)
        path_world.append((wx, wy))

    # Subsample path — don't need a waypoint for every cell
    if len(path_world) > 5:
        step = max(1, len(path_world) // 20)
        subsampled = path_world[::step]
        if subsampled[-1] != path_world[-1]:
            subsampled.append(path_world[-1])
        return subsampled

    return path_world
