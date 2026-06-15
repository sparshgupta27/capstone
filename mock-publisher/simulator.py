"""
Simulator module — robot motion model, floor plan, LiDAR raycast, object detection.
All simulation logic is self-contained here; publisher.py handles networking.
"""
import math
import random
import json
import time

# Load config
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

WALLS = CONFIG['floor_plan']['walls']
FLOOR_W = CONFIG['floor_plan']['width']
FLOOR_H = CONFIG['floor_plan']['height']
LIDAR_RAYS = CONFIG['lidar']['num_rays']
LIDAR_MAX = CONFIG['lidar']['max_range']
LIDAR_NOISE = CONFIG['lidar']['noise_std']
OBJECTS = CONFIG['detectable_objects']

# ── Wall Geometry ─────────────────────────────────────────────

def segments():
    """Convert wall definitions to line segments [(x1,y1,x2,y2), ...]"""
    return [(w['x1'], w['y1'], w['x2'], w['y2']) for w in WALLS]

WALL_SEGMENTS = segments()

def ray_segment_intersect(ox, oy, dx, dy, x1, y1, x2, y2):
    """
    Ray-segment intersection. Returns distance t along ray, or None.
    Ray: origin (ox,oy), direction (dx,dy)
    Segment: (x1,y1) to (x2,y2)
    """
    denom = dx * (y2 - y1) - dy * (x2 - x1)
    if abs(denom) < 1e-10:
        return None
    t = ((x1 - ox) * (y2 - y1) - (y1 - oy) * (x2 - x1)) / denom
    u = ((x1 - ox) * (-dy) - (y1 - oy) * (-dx)) / denom
    if t > 0 and 0 <= u <= 1:
        return t
    return None


# ── Robot State ───────────────────────────────────────────────

class Robot:
    def __init__(self):
        self.x = CONFIG['robot']['start_x']
        self.y = CONFIG['robot']['start_y']
        self.theta = CONFIG['robot']['start_theta']
        self.vx = 0.0
        self.vtheta = 0.0
        self.max_speed = CONFIG['robot']['max_speed']
        self.max_angular = CONFIG['robot']['max_angular_speed']
        self.radius = CONFIG['robot']['radius']
        self.battery = 100.0
        self.state = 'exploring'
        self.target = None
        self._pick_target()

    def _pick_target(self):
        """Pick a random free-space target to navigate toward"""
        for _ in range(100):
            tx = random.uniform(1, FLOOR_W - 1)
            ty = random.uniform(1, FLOOR_H - 1)
            # Simple check: not inside a wall
            if self._is_free(tx, ty):
                self.target = (tx, ty)
                return
        self.target = (FLOOR_W / 2, FLOOR_H / 2)

    def _is_free(self, x, y):
        """Quick check: is this point reasonably far from all walls?"""
        for x1, y1, x2, y2 in WALL_SEGMENTS:
            dist = point_to_segment_dist(x, y, x1, y1, x2, y2)
            if dist < self.radius * 2:
                return False
        return True

    def update(self, dt):
        """Advance robot by dt seconds using differential drive toward target."""
        if self.target is None:
            self._pick_target()

        tx, ty = self.target
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.5:
            # Reached target, pick new one
            self._pick_target()
            return

        # Desired heading
        desired_theta = math.atan2(dy, dx)
        angle_diff = normalize_angle(desired_theta - self.theta)

        # Proportional control
        self.vtheta = max(-self.max_angular, min(self.max_angular, angle_diff * 2.0))

        # Slow down when turning sharply
        turn_factor = max(0.1, 1.0 - abs(angle_diff) / math.pi)
        self.vx = self.max_speed * turn_factor

        # Check for obstacles ahead using a few forward rays
        min_front_dist = self._front_clearance()
        if min_front_dist < 0.8:
            # Obstacle avoidance: slow down and turn away
            self.vx *= 0.2
            self.vtheta += (1.0 if random.random() > 0.5 else -1.0) * self.max_angular * 0.5

        # Apply motion
        new_theta = self.theta + self.vtheta * dt
        new_x = self.x + self.vx * math.cos(new_theta) * dt
        new_y = self.y + self.vx * math.sin(new_theta) * dt

        # Wall collision check
        if self._is_free(new_x, new_y):
            self.x = max(self.radius, min(FLOOR_W - self.radius, new_x))
            self.y = max(self.radius, min(FLOOR_H - self.radius, new_y))
            self.theta = normalize_angle(new_theta)
        else:
            # Bounce: pick new target
            self._pick_target()
            self.vtheta = self.max_angular * (1 if random.random() > 0.5 else -1)
            self.vx = 0

        # Battery drain
        self.battery = max(0, self.battery - 0.008 * dt)  # ~0.5%/min
        if self.battery < 10:
            self.state = 'returning'
        elif self.battery <= 0:
            self.state = 'idle'

    def _front_clearance(self):
        """Measure closest obstacle in a ±30° cone ahead"""
        min_dist = LIDAR_MAX
        for offset in [-0.5, -0.25, 0, 0.25, 0.5]:
            angle = self.theta + offset
            dx = math.cos(angle)
            dy = math.sin(angle)
            for seg in WALL_SEGMENTS:
                t = ray_segment_intersect(self.x, self.y, dx, dy, *seg)
                if t is not None and t < min_dist:
                    min_dist = t
        return min_dist

    def get_odom(self):
        return {
            'type': 'odom',
            'x': round(self.x, 4),
            'y': round(self.y, 4),
            'theta': round(self.theta, 4),
            'vx': round(self.vx, 4),
            'vtheta': round(self.vtheta, 4),
            'timestamp': time.time() * 1000,
        }

    def get_battery(self):
        return {
            'type': 'battery',
            'level': round(self.battery, 1),
            'charging': False,
            'timestamp': time.time() * 1000,
        }

    def get_status(self):
        speed = round(math.sqrt(self.vx ** 2) * 100) / 100
        return {
            'type': 'status',
            'state': self.state,
            'speed': speed,
            'timestamp': time.time() * 1000,
        }


# ── LiDAR Simulation ─────────────────────────────────────────

def scan_lidar(robot):
    """Simulate a 360-degree LiDAR scan from robot's position"""
    ranges = []
    angle_inc = 2 * math.pi / LIDAR_RAYS

    for i in range(LIDAR_RAYS):
        angle = robot.theta + i * angle_inc
        dx = math.cos(angle)
        dy = math.sin(angle)

        min_dist = LIDAR_MAX
        for seg in WALL_SEGMENTS:
            t = ray_segment_intersect(robot.x, robot.y, dx, dy, *seg)
            if t is not None and t < min_dist:
                min_dist = t

        # Add Gaussian noise
        noisy = min_dist + random.gauss(0, LIDAR_NOISE)
        ranges.append(round(max(0, min(LIDAR_MAX, noisy)), 3))

    return {
        'type': 'lidar',
        'ranges': ranges,
        'angle_min': 0,
        'angle_max': 2 * math.pi,
        'angle_increment': angle_inc,
        'range_max': LIDAR_MAX,
        'timestamp': time.time() * 1000,
    }


# ── Object Detection Simulation ──────────────────────────────

def simulate_detection(robot):
    """Randomly generate a YOLO-style detection near the robot"""
    label = random.choice(OBJECTS)
    confidence = round(random.uniform(0.45, 0.98), 2)

    # Place detection within LiDAR range in front of robot
    dist = random.uniform(0.5, 4.0)
    angle = robot.theta + random.uniform(-0.8, 0.8)
    wx = robot.x + dist * math.cos(angle)
    wy = robot.y + dist * math.sin(angle)

    # Fake bounding box (in image coordinates, as if from a camera)
    bx = random.randint(50, 500)
    by = random.randint(50, 400)
    bw = random.randint(40, 200)
    bh = random.randint(40, 200)

    return {
        'type': 'detection',
        'label': label,
        'confidence': confidence,
        'bbox': {'x': bx, 'y': by, 'w': bw, 'h': bh},
        'world_pos': {'x': round(wx, 3), 'y': round(wy, 3)},
        'timestamp': time.time() * 1000,
    }


# ── Occupancy Grid ────────────────────────────────────────────

def build_occupancy_grid(robot, resolution=0.5):
    """
    Build a simple occupancy grid based on the floor plan + LiDAR.
    Cells near walls = occupied, cells far from walls = free, far from robot = unknown.
    """
    w = int(FLOOR_W / resolution)
    h = int(FLOOR_H / resolution)
    grid = [-1] * (w * h)  # start unknown

    explore_radius = 6.0  # how far the robot can "see"

    for gy in range(h):
        for gx in range(w):
            cx = (gx + 0.5) * resolution
            cy = (gy + 0.5) * resolution

            # Distance from robot
            dist_to_robot = math.sqrt((cx - robot.x) ** 2 + (cy - robot.y) ** 2)
            if dist_to_robot > explore_radius:
                continue  # leave as unknown

            # Check if near a wall
            near_wall = False
            for x1, y1, x2, y2 in WALL_SEGMENTS:
                d = point_to_segment_dist(cx, cy, x1, y1, x2, y2)
                if d < resolution:
                    near_wall = True
                    break

            grid[gy * w + gx] = 1 if near_wall else 0

    return {
        'type': 'grid',
        'width': w,
        'height': h,
        'resolution': resolution,
        'origin': {'x': 0, 'y': 0},
        'data': grid,
        'timestamp': time.time() * 1000,
    }


# ── Utilities ─────────────────────────────────────────────────

def normalize_angle(a):
    """Normalize angle to [-pi, pi]"""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    """Distance from point (px,py) to line segment (x1,y1)-(x2,y2)"""
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
