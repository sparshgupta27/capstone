"""
SLAM Engine — Simultaneous Localization and Mapping

Combines scan matching (ICP) with occupancy grid mapping:
1. Receive new LiDAR scan
2. Match against previous scan to estimate motion (scan matching)
3. Correct robot pose using the scan match result
4. Update the occupancy grid map with the corrected pose + scan
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import LIDAR_MAX_RANGE, LIDAR_NUM_RAYS
from brain.slam.occupancy_grid import OccupancyGrid
from brain.slam.scan_matcher import icp_match, polar_to_cartesian, transform_points


class SLAMEngine:
    """
    Simple 2D SLAM engine using ICP scan matching + occupancy grid mapping.

    For a real production system you'd use GMapping, Cartographer, or RTAB-Map.
    This is a teaching implementation that demonstrates the core concepts.
    """

    def __init__(self):
        self.map = OccupancyGrid()
        self.pose = [0.0, 0.0, 0.0]  # [x, y, theta] in world frame
        self.prev_scan_points = None   # previous scan in robot frame
        self.scan_count = 0

    def update(self, ranges, odom_dx=0.0, odom_dy=0.0, odom_dtheta=0.0):
        """
        Process a new LiDAR scan and update the map.

        Args:
            ranges: List of range measurements from LiDAR
            odom_dx, odom_dy, odom_dtheta: Odometry-predicted motion since last update

        Returns:
            corrected_pose: [x, y, theta] — the SLAM-corrected robot pose
        """
        num_rays = len(ranges)
        angle_increment = 2 * math.pi / num_rays

        # Convert polar scan to cartesian points in robot frame
        current_points = polar_to_cartesian(ranges, 0.0, angle_increment, LIDAR_MAX_RANGE)

        # Apply odometry prediction
        self.pose[0] += odom_dx * math.cos(self.pose[2]) - odom_dy * math.sin(self.pose[2])
        self.pose[1] += odom_dx * math.sin(self.pose[2]) + odom_dy * math.cos(self.pose[2])
        self.pose[2] += odom_dtheta
        # Normalize angle
        self.pose[2] = math.atan2(math.sin(self.pose[2]), math.cos(self.pose[2]))

        # Scan matching correction (skip for first scan)
        if self.prev_scan_points is not None and len(current_points) > 20:
            (dx, dy, dtheta), error = icp_match(current_points, self.prev_scan_points)

            # Only apply correction if the match quality is good
            if error < 0.5:
                # Blend scan match correction with odometry (trust scan match more)
                alpha = 0.7  # weight for scan match correction
                self.pose[0] += alpha * dx
                self.pose[1] += alpha * dy
                self.pose[2] += alpha * dtheta
                self.pose[2] = math.atan2(math.sin(self.pose[2]), math.cos(self.pose[2]))

        # Update the occupancy grid with the corrected pose
        self.map.update_from_scan(
            self.pose[0], self.pose[1], self.pose[2],
            ranges, angle_min=0.0, angle_increment=angle_increment
        )

        # Store current scan for next iteration
        self.prev_scan_points = current_points
        self.scan_count += 1

        return list(self.pose)

    def get_pose(self):
        """Get current SLAM-corrected pose [x, y, theta]."""
        return list(self.pose)

    def get_map(self):
        """Get the occupancy grid map object."""
        return self.map

    def get_map_dict(self):
        """Get map as dictionary for WebSocket transmission."""
        d = self.map.to_dict()
        d['timestamp'] = None  # caller fills this in
        return d

    def set_pose(self, x, y, theta):
        """Manually set the robot pose (e.g., from external localization)."""
        self.pose = [x, y, theta]
