"""
Simulated World — Floor plan, physics, and sensor simulation.

This replaces the mock-publisher entirely. The brain runs its algorithms
against this simulated environment. When real hardware arrives, swap
SimLiDAR for RPLiDAR, SimMotors for GPIOMotors — brain code unchanged.
"""
import math
import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    SIM_WALLS, SIM_FLOOR_WIDTH, SIM_FLOOR_HEIGHT, SIM_DT,
    LIDAR_NUM_RAYS, LIDAR_MAX_RANGE, LIDAR_NOISE_STD,
    WHEEL_BASE, SIM_OBJECTS,
)
from brain.hardware.interfaces import LiDARInterface, MotorInterface, CameraInterface, IMUInterface


# ── Geometry Helpers ──────────────────────────────────────────

def ray_segment_intersect(ox, oy, dx, dy, x1, y1, x2, y2):
    """Ray-segment intersection. Returns distance or None."""
    denom = dx * (y2 - y1) - dy * (x2 - x1)
    if abs(denom) < 1e-10:
        return None
    t = ((x1 - ox) * (y2 - y1) - (y1 - oy) * (x2 - x1)) / denom
    u = ((x1 - ox) * (-dy) - (y1 - oy) * (-dx)) / denom
    if t > 0.001 and 0 <= u <= 1:
        return t
    return None


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    """Distance from point to line segment."""
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    proj_x, proj_y = x1 + t * dx, y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


# ── Simulated Robot State ─────────────────────────────────────

class SimRobot:
    """The simulated physical robot — tracks position and responds to motor commands."""

    def __init__(self, x=2.5, y=3.5, theta=0.0):
        self.x = x
        self.y = y
        self.theta = theta
        self.v_left = 0.0
        self.v_right = 0.0
        self.battery = 100.0

    def set_wheel_speeds(self, v_left, v_right):
        self.v_left = v_left
        self.v_right = v_right

    def step(self, dt):
        """Advance physics by dt seconds."""
        v = (self.v_left + self.v_right) / 2.0
        w = (self.v_right - self.v_left) / WHEEL_BASE

        new_theta = self.theta + w * dt
        new_x = self.x + v * math.cos(new_theta) * dt
        new_y = self.y + v * math.sin(new_theta) * dt

        # Wall collision check
        if self._is_valid(new_x, new_y):
            self.x = max(0.2, min(SIM_FLOOR_WIDTH - 0.2, new_x))
            self.y = max(0.2, min(SIM_FLOOR_HEIGHT - 0.2, new_y))
            self.theta = math.atan2(math.sin(new_theta), math.cos(new_theta))

        # Battery drain
        speed = abs(v)
        self.battery = max(0, self.battery - (0.005 + speed * 0.01) * dt)

    def _is_valid(self, x, y):
        for wall in SIM_WALLS:
            if point_to_segment_dist(x, y, *wall) < 0.25:
                return False
        return True


# ── Simulated LiDAR ──────────────────────────────────────────

class SimLiDAR(LiDARInterface):
    """Simulated LiDAR — raycasts against the floor plan walls."""

    def __init__(self, robot):
        self.robot = robot
        self.num_rays = LIDAR_NUM_RAYS

    def get_scan(self):
        ranges = []
        angle_inc = 2 * math.pi / self.num_rays

        for i in range(self.num_rays):
            angle = self.robot.theta + i * angle_inc
            dx = math.cos(angle)
            dy = math.sin(angle)

            min_dist = LIDAR_MAX_RANGE
            for wall in SIM_WALLS:
                t = ray_segment_intersect(self.robot.x, self.robot.y, dx, dy, *wall)
                if t is not None and t < min_dist:
                    min_dist = t

            # Add noise
            noisy = min_dist + random.gauss(0, LIDAR_NOISE_STD)
            ranges.append(max(0.0, min(LIDAR_MAX_RANGE, noisy)))

        return ranges

    def get_num_rays(self):
        return self.num_rays


# ── Simulated Motors ──────────────────────────────────────────

class SimMotors(MotorInterface):
    """Simulated motors — directly control the simulated robot."""

    def __init__(self, robot):
        self.robot = robot

    def set_speeds(self, left_speed, right_speed):
        self.robot.set_wheel_speeds(left_speed, right_speed)

    def get_encoder_velocities(self):
        # Add small noise to simulate encoder imperfection
        noise = 0.01
        return (
            self.robot.v_left + random.gauss(0, noise),
            self.robot.v_right + random.gauss(0, noise),
        )

    def stop(self):
        self.robot.set_wheel_speeds(0, 0)


# ── Simulated Camera (YOLO detections) ───────────────────────

class SimCamera(CameraInterface):
    """Simulated camera — generates random object detections."""

    def __init__(self, robot):
        self.robot = robot
        self._last_detection_time = 0
        self._detection_interval = random.uniform(2, 6)

    def get_frame(self):
        """Returns None (no actual image in simulation)."""
        return None

    def detect_objects(self):
        """Generate simulated object detections in front of the robot."""
        import time
        now = time.time()
        if now - self._last_detection_time < self._detection_interval:
            return []

        self._last_detection_time = now
        self._detection_interval = random.uniform(2, 8)

        # Random detection
        label = random.choice(SIM_OBJECTS)
        confidence = round(random.uniform(0.5, 0.98), 2)
        dist = random.uniform(0.5, 3.0)
        angle = self.robot.theta + random.uniform(-0.6, 0.6)
        wx = self.robot.x + dist * math.cos(angle)
        wy = self.robot.y + dist * math.sin(angle)

        return [{
            'label': label,
            'confidence': confidence,
            'world_pos': {'x': round(wx, 3), 'y': round(wy, 3)},
            'bbox': {'x': random.randint(50, 500), 'y': random.randint(50, 400),
                     'w': random.randint(40, 200), 'h': random.randint(40, 200)},
        }]


# ── Simulated IMU ─────────────────────────────────────────────

class SimIMU(IMUInterface):
    """Simulated IMU — returns robot orientation with noise."""

    def __init__(self, robot):
        self.robot = robot

    def get_orientation(self):
        return (0.0, 0.0, self.robot.theta + random.gauss(0, 0.005))

    def get_angular_velocity(self):
        w = (self.robot.v_right - self.robot.v_left) / WHEEL_BASE
        return (0.0, 0.0, w + random.gauss(0, 0.01))
