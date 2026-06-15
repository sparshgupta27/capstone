"""
Extended Kalman Filter (EKF) — Sensor fusion for robot localization.

Fuses multiple noisy measurements (odometry, SLAM scan match, IMU)
into a single best estimate of the robot's pose.

State vector: [x, y, theta]
Prediction: Uses differential drive kinematics (from motor commands)
Update: Uses SLAM scan match corrections (from ICP)

The EKF handles the fact that all sensors are noisy:
  - Wheel encoders drift over time (slip, uneven ground)
  - SLAM scan matching can fail in featureless areas
  - IMU gyroscope has bias drift
  - The EKF weighs each source based on its uncertainty
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import EKF_PROCESS_NOISE, EKF_MEASUREMENT_NOISE


class ExtendedKalmanFilter:
    """
    EKF for 2D robot pose estimation.
    State: [x, y, theta]
    """

    def __init__(self):
        # State estimate [x, y, theta]
        self.state = [0.0, 0.0, 0.0]

        # Covariance matrix (3x3) — starts with high uncertainty
        self.P = [
            [0.1, 0.0, 0.0],
            [0.0, 0.1, 0.0],
            [0.0, 0.0, 0.05],
        ]

        # Process noise
        self.Q = [
            [EKF_PROCESS_NOISE[0] ** 2, 0, 0],
            [0, EKF_PROCESS_NOISE[1] ** 2, 0],
            [0, 0, EKF_PROCESS_NOISE[2] ** 2],
        ]

        # Measurement noise
        self.R = [
            [EKF_MEASUREMENT_NOISE[0] ** 2, 0, 0],
            [0, EKF_MEASUREMENT_NOISE[1] ** 2, 0],
            [0, 0, EKF_MEASUREMENT_NOISE[2] ** 2],
        ]

    def predict(self, v, w, dt):
        """
        Prediction step — propagate state using motion model.

        Args:
            v: Linear velocity command (m/s)
            w: Angular velocity command (rad/s)
            dt: Time step (seconds)
        """
        x, y, theta = self.state

        # Motion model: differential drive kinematics
        if abs(w) < 1e-6:
            # Straight line
            dx = v * math.cos(theta) * dt
            dy = v * math.sin(theta) * dt
            dtheta = 0.0
        else:
            # Arc
            dx = -v / w * math.sin(theta) + v / w * math.sin(theta + w * dt)
            dy = v / w * math.cos(theta) - v / w * math.cos(theta + w * dt)
            dtheta = w * dt

        # Update state prediction
        self.state[0] = x + dx
        self.state[1] = y + dy
        self.state[2] = _normalize_angle(theta + dtheta)

        # Jacobian of the motion model with respect to state
        G = [
            [1, 0, -v * math.sin(theta) * dt if abs(w) < 1e-6
                else -v / w * math.cos(theta) + v / w * math.cos(theta + w * dt)],
            [0, 1, v * math.cos(theta) * dt if abs(w) < 1e-6
                else -v / w * math.sin(theta) + v / w * math.sin(theta + w * dt)],
            [0, 0, 1],
        ]

        # Update covariance: P = G * P * G^T + Q
        self.P = _mat_add(_mat_mul(_mat_mul(G, self.P), _mat_transpose(G)), self.Q)

    def update(self, measured_x, measured_y, measured_theta):
        """
        Update step — correct state using a measurement (e.g., from SLAM scan matching).

        Args:
            measured_x, measured_y, measured_theta: Measured pose from SLAM
        """
        # Innovation (measurement residual)
        z = [measured_x, measured_y, measured_theta]
        y_innov = [
            z[0] - self.state[0],
            z[1] - self.state[1],
            _normalize_angle(z[2] - self.state[2]),
        ]

        # Measurement model is identity (we directly measure the state)
        # H = I (identity matrix)
        # Innovation covariance: S = H * P * H^T + R = P + R
        S = _mat_add(self.P, self.R)

        # Kalman gain: K = P * H^T * S^-1 = P * S^-1
        S_inv = _mat_inv_3x3(S)
        if S_inv is None:
            return  # Singular matrix — skip update

        K = _mat_mul(self.P, S_inv)

        # Update state: x = x + K * y
        for i in range(3):
            correction = sum(K[i][j] * y_innov[j] for j in range(3))
            self.state[i] += correction
        self.state[2] = _normalize_angle(self.state[2])

        # Update covariance: P = (I - K * H) * P = (I - K) * P
        I_KH = [
            [1 - K[0][0], -K[0][1], -K[0][2]],
            [-K[1][0], 1 - K[1][1], -K[1][2]],
            [-K[2][0], -K[2][1], 1 - K[2][2]],
        ]
        self.P = _mat_mul(I_KH, self.P)

    def get_pose(self):
        """Get current estimated pose [x, y, theta]."""
        return list(self.state)

    def set_pose(self, x, y, theta):
        """Manually set pose (e.g., at initialization)."""
        self.state = [x, y, theta]

    def get_uncertainty(self):
        """Get position uncertainty (standard deviation in meters)."""
        return math.sqrt(self.P[0][0] + self.P[1][1])


# ── 3x3 Matrix helpers (no numpy dependency) ──────────────────

def _normalize_angle(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def _mat_mul(A, B):
    """Multiply two 3x3 matrices."""
    result = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i][j] += A[i][k] * B[k][j]
    return result


def _mat_add(A, B):
    return [[A[i][j] + B[i][j] for j in range(3)] for i in range(3)]


def _mat_transpose(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]


def _mat_inv_3x3(m):
    """Invert a 3x3 matrix. Returns None if singular."""
    det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
         - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
         + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))

    if abs(det) < 1e-12:
        return None

    inv_det = 1.0 / det
    return [
        [(m[1][1]*m[2][2] - m[1][2]*m[2][1]) * inv_det,
         (m[0][2]*m[2][1] - m[0][1]*m[2][2]) * inv_det,
         (m[0][1]*m[1][2] - m[0][2]*m[1][1]) * inv_det],
        [(m[1][2]*m[2][0] - m[1][0]*m[2][2]) * inv_det,
         (m[0][0]*m[2][2] - m[0][2]*m[2][0]) * inv_det,
         (m[0][2]*m[1][0] - m[0][0]*m[1][2]) * inv_det],
        [(m[1][0]*m[2][1] - m[1][1]*m[2][0]) * inv_det,
         (m[0][1]*m[2][0] - m[0][0]*m[2][1]) * inv_det,
         (m[0][0]*m[1][1] - m[0][1]*m[1][0]) * inv_det],
    ]
