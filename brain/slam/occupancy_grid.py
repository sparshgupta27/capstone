"""
Occupancy Grid Map — Probabilistic mapping using log-odds.

Each cell stores a log-odds value representing the probability of being occupied:
  - log-odds > 0 → likely occupied
  - log-odds < 0 → likely free
  - log-odds = 0 → unknown

When a LiDAR ray passes through a cell, we decrease its log-odds (it's free).
When a LiDAR ray terminates at a cell, we increase its log-odds (it's occupied).
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    MAP_RESOLUTION, MAP_WIDTH, MAP_HEIGHT, MAP_ORIGIN_X, MAP_ORIGIN_Y,
    LOG_ODDS_PRIOR, LOG_ODDS_OCC, LOG_ODDS_FREE, LOG_ODDS_MAX, LOG_ODDS_MIN,
    OBSTACLE_INFLATION_RADIUS, LIDAR_MAX_RANGE,
)


class OccupancyGrid:
    """
    2D probabilistic occupancy grid for robot mapping.
    Uses log-odds representation for efficient Bayesian updates.
    """

    def __init__(self, width=MAP_WIDTH, height=MAP_HEIGHT, resolution=MAP_RESOLUTION,
                 origin_x=MAP_ORIGIN_X, origin_y=MAP_ORIGIN_Y):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.origin_x = origin_x
        self.origin_y = origin_y

        # Log-odds grid — initialized to prior (unknown)
        self.grid = [[LOG_ODDS_PRIOR] * width for _ in range(height)]

        # Pre-compute log-odds update values
        self._log_occ = math.log(LOG_ODDS_OCC / (1 - LOG_ODDS_OCC))
        self._log_free = math.log(LOG_ODDS_FREE / (1 - LOG_ODDS_FREE))

    def world_to_grid(self, wx, wy):
        """Convert world coordinates (meters) to grid cell indices."""
        gx = int((wx - self.origin_x) / self.resolution)
        gy = int((wy - self.origin_y) / self.resolution)
        return gx, gy

    def grid_to_world(self, gx, gy):
        """Convert grid cell indices to world coordinates (center of cell)."""
        wx = self.origin_x + (gx + 0.5) * self.resolution
        wy = self.origin_y + (gy + 0.5) * self.resolution
        return wx, wy

    def in_bounds(self, gx, gy):
        """Check if grid coordinates are within map bounds."""
        return 0 <= gx < self.width and 0 <= gy < self.height

    def get_probability(self, gx, gy):
        """Get occupancy probability [0, 1] for a cell."""
        if not self.in_bounds(gx, gy):
            return 0.5  # unknown
        lo = self.grid[gy][gx]
        return 1.0 - 1.0 / (1.0 + math.exp(lo))

    def is_occupied(self, gx, gy):
        """Check if a cell is occupied (probability > 0.65)."""
        return self.get_probability(gx, gy) > 0.65

    def is_free(self, gx, gy):
        """Check if a cell is free (probability < 0.35)."""
        return self.in_bounds(gx, gy) and self.get_probability(gx, gy) < 0.35

    def is_unknown(self, gx, gy):
        """Check if a cell is unknown (probability ≈ 0.5)."""
        if not self.in_bounds(gx, gy):
            return True
        p = self.get_probability(gx, gy)
        return 0.35 <= p <= 0.65

    def update_cell(self, gx, gy, occupied):
        """Update a single cell with a new observation using Bayesian log-odds."""
        if not self.in_bounds(gx, gy):
            return
        if occupied:
            self.grid[gy][gx] += self._log_occ
        else:
            self.grid[gy][gx] += self._log_free
        # Clamp to prevent overconfidence
        self.grid[gy][gx] = max(LOG_ODDS_MIN, min(LOG_ODDS_MAX, self.grid[gy][gx]))

    def update_from_scan(self, robot_x, robot_y, robot_theta, ranges, angle_min=0.0, angle_increment=None):
        """
        Update the entire grid from a LiDAR scan using Bresenham ray tracing.

        Args:
            robot_x, robot_y: Robot position in world coordinates (meters)
            robot_theta: Robot heading (radians)
            ranges: List of range measurements (meters)
            angle_min: Starting angle of the scan (radians, relative to robot)
            angle_increment: Angle between consecutive rays (radians)
        """
        num_rays = len(ranges)
        if angle_increment is None:
            angle_increment = 2 * math.pi / num_rays

        rx, ry = self.world_to_grid(robot_x, robot_y)

        for i in range(num_rays):
            angle = robot_theta + angle_min + i * angle_increment
            r = ranges[i]

            if r <= 0 or r >= LIDAR_MAX_RANGE:
                continue

            # Endpoint of the ray in world coordinates
            hit_x = robot_x + r * math.cos(angle)
            hit_y = robot_y + r * math.sin(angle)
            hx, hy = self.world_to_grid(hit_x, hit_y)

            # Trace the ray using Bresenham's algorithm
            cells = self._bresenham(rx, ry, hx, hy)

            # All cells along the ray (except the last) are free
            for cx, cy in cells[:-1]:
                self.update_cell(cx, cy, occupied=False)

            # The endpoint cell is occupied
            if self.in_bounds(hx, hy):
                self.update_cell(hx, hy, occupied=True)

    def _bresenham(self, x0, y0, x1, y1):
        """Bresenham's line algorithm — returns list of (x, y) grid cells along the line."""
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if self.in_bounds(x0, y0):
                cells.append((x0, y0))

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return cells

    def get_inflated_grid(self):
        """
        Return a binary grid with obstacles inflated by the robot radius.
        Used for path planning to ensure the robot doesn't clip walls.
        Returns: 2D list where True = blocked, False = passable
        """
        inflated = [[False] * self.width for _ in range(self.height)]
        r = OBSTACLE_INFLATION_RADIUS

        for gy in range(self.height):
            for gx in range(self.width):
                if self.is_occupied(gx, gy):
                    # Inflate: mark all cells within radius as blocked
                    for dy in range(-r, r + 1):
                        for dx in range(-r, r + 1):
                            nx, ny = gx + dx, gy + dy
                            if self.in_bounds(nx, ny) and dx * dx + dy * dy <= r * r:
                                inflated[ny][nx] = True

        return inflated

    def to_array(self):
        """
        Export grid as a flat array for transmission.
        Values: 0 = free, 1 = occupied, -1 = unknown
        """
        data = []
        for gy in range(self.height):
            for gx in range(self.width):
                p = self.get_probability(gx, gy)
                if p > 0.65:
                    data.append(1)
                elif p < 0.35:
                    data.append(0)
                else:
                    data.append(-1)
        return data

    def to_dict(self):
        """Export grid as a dictionary for WebSocket transmission."""
        return {
            'type': 'grid',
            'width': self.width,
            'height': self.height,
            'resolution': self.resolution,
            'origin': {'x': self.origin_x, 'y': self.origin_y},
            'data': self.to_array(),
        }
