"""
Rover Brain — Central Configuration
All tunable parameters in one place. Change these for your specific hardware.
"""
import math

# ══════════════════════════════════════════════════════════════
# ROBOT PHYSICAL PARAMETERS
# ══════════════════════════════════════════════════════════════
WHEEL_BASE = 0.30           # distance between wheels (meters)
WHEEL_RADIUS = 0.033        # wheel radius (meters)
ROBOT_RADIUS = 0.18         # robot footprint radius for collision checking
MAX_LINEAR_VEL = 0.5        # max forward speed (m/s)
MAX_ANGULAR_VEL = 1.5       # max rotation speed (rad/s)
MAX_LINEAR_ACC = 0.8        # max linear acceleration (m/s²)
MAX_ANGULAR_ACC = 2.0       # max angular acceleration (rad/s²)

# ══════════════════════════════════════════════════════════════
# LIDAR PARAMETERS
# ══════════════════════════════════════════════════════════════
LIDAR_NUM_RAYS = 360        # number of rays per scan
LIDAR_MAX_RANGE = 8.0       # max detection range (meters)
LIDAR_MIN_RANGE = 0.15      # min detection range (meters)
LIDAR_NOISE_STD = 0.02      # range measurement noise std dev (meters)
LIDAR_ANGLE_MIN = 0.0       # start angle (radians)
LIDAR_ANGLE_MAX = 2 * math.pi  # end angle (radians)

# ══════════════════════════════════════════════════════════════
# OCCUPANCY GRID / MAPPING
# ══════════════════════════════════════════════════════════════
MAP_RESOLUTION = 0.1        # meters per cell (10cm)
MAP_WIDTH = 200             # grid cells (200 * 0.1 = 20m)
MAP_HEIGHT = 200            # grid cells
MAP_ORIGIN_X = 0.0          # world x of grid origin
MAP_ORIGIN_Y = 0.0          # world y of grid origin

# Log-odds parameters for Bayesian occupancy update
LOG_ODDS_PRIOR = 0.0        # prior (unknown)
LOG_ODDS_OCC = 0.85         # probability of occupied given hit
LOG_ODDS_FREE = 0.4         # probability of occupied given pass-through
LOG_ODDS_MAX = 5.0          # clamp to prevent overconfidence
LOG_ODDS_MIN = -5.0

OBSTACLE_INFLATION_RADIUS = 3  # cells to inflate obstacles for path planning

# ══════════════════════════════════════════════════════════════
# SLAM / SCAN MATCHING
# ══════════════════════════════════════════════════════════════
ICP_MAX_ITERATIONS = 50
ICP_TOLERANCE = 1e-5        # convergence threshold
ICP_MAX_CORRESPONDENCE_DIST = 0.5  # max distance to match points (meters)

# ══════════════════════════════════════════════════════════════
# A* PATH PLANNER
# ══════════════════════════════════════════════════════════════
ASTAR_ALLOW_DIAGONAL = True
ASTAR_WEIGHT = 1.0          # heuristic weight (1.0 = optimal, >1 = faster but suboptimal)

# ══════════════════════════════════════════════════════════════
# DWA LOCAL PLANNER
# ══════════════════════════════════════════════════════════════
DWA_DT = 0.1                # simulation timestep (seconds)
DWA_PREDICT_TIME = 1.5      # how far ahead to simulate (seconds)
DWA_V_SAMPLES = 15          # number of linear velocity samples
DWA_W_SAMPLES = 25          # number of angular velocity samples
DWA_GOAL_WEIGHT = 1.0       # weight for heading toward goal
DWA_OBSTACLE_WEIGHT = 0.5   # weight for obstacle clearance
DWA_SPEED_WEIGHT = 0.3      # weight for forward speed
DWA_MIN_OBSTACLE_DIST = 0.2 # minimum clearance from obstacles (meters)

# ══════════════════════════════════════════════════════════════
# FRONTIER EXPLORATION
# ══════════════════════════════════════════════════════════════
FRONTIER_MIN_SIZE = 3       # minimum frontier cluster size (cells)
FRONTIER_DISTANCE_WEIGHT = 1.0
FRONTIER_SIZE_WEIGHT = 2.0  # prefer larger frontiers

# ══════════════════════════════════════════════════════════════
# PID CONTROLLER
# ══════════════════════════════════════════════════════════════
PID_KP = 2.0                # proportional gain
PID_KI = 0.1                # integral gain
PID_KD = 0.05               # derivative gain
PID_MAX_OUTPUT = 255         # max PWM value
PID_INTEGRAL_LIMIT = 50.0   # anti-windup clamp

# ══════════════════════════════════════════════════════════════
# EXTENDED KALMAN FILTER
# ══════════════════════════════════════════════════════════════
EKF_PROCESS_NOISE = [0.02, 0.02, 0.01]   # [x, y, theta] process noise
EKF_MEASUREMENT_NOISE = [0.05, 0.05, 0.02]  # [x, y, theta] measurement noise from SLAM

# ══════════════════════════════════════════════════════════════
# STATE MACHINE
# ══════════════════════════════════════════════════════════════
WAYPOINT_REACHED_THRESHOLD = 0.3   # distance to consider waypoint reached (meters)
BATTERY_CRITICAL_LEVEL = 10.0      # % to trigger emergency return
STUCK_TIMEOUT = 10.0               # seconds without movement → re-plan

# ══════════════════════════════════════════════════════════════
# SIMULATION
# ══════════════════════════════════════════════════════════════
SIM_DT = 0.02               # simulation physics timestep (50Hz)
SIM_FLOOR_WIDTH = 20.0       # meters
SIM_FLOOR_HEIGHT = 20.0      # meters

# Wall definitions: list of (x1, y1, x2, y2) line segments
SIM_WALLS = [
    # Outer walls
    (0, 0, 20, 0), (20, 0, 20, 20), (20, 20, 0, 20), (0, 20, 0, 0),
    # Inner walls — rooms and corridors
    (0, 7, 5, 7), (7, 7, 12, 7),
    (5, 0, 5, 5), (12, 0, 12, 5),
    (12, 7, 12, 14),
    (0, 14, 8, 14), (10, 14, 20, 14),
    (15, 7, 15, 14), (15, 7, 20, 7),
]

# Detectable objects for YOLO simulation
SIM_OBJECTS = [
    "chair", "desk", "door", "fire_extinguisher", "person",
    "box", "trash_bin", "monitor", "bookshelf", "plant"
]

# ══════════════════════════════════════════════════════════════
# NETWORKING
# ══════════════════════════════════════════════════════════════
BACKEND_WS_URL = "ws://localhost:5000"
TELEMETRY_PUBLISH_HZ = 10   # odometry publish rate
MAP_PUBLISH_HZ = 0.5        # map snapshot publish rate
