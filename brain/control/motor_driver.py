"""
Motor Driver — Differential drive kinematics and motor interface.

Converts (v, w) velocity commands to individual wheel speeds,
then uses PID controllers to track those speeds.

On real hardware:
  - This would output PWM to an L298N or similar motor driver via GPIO
  - Wheel encoders provide actual velocity feedback for the PID loop

In simulation:
  - Directly applies velocities to the simulated robot
"""
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import WHEEL_BASE, MAX_LINEAR_VEL, MAX_ANGULAR_VEL
from brain.control.pid import PIDController


class MotorDriver:
    """
    Differential drive motor controller.
    Manages two PID controllers (left/right wheel) and converts
    unicycle commands (v, w) to wheel velocities.
    """

    def __init__(self, wheel_base=WHEEL_BASE):
        self.wheel_base = wheel_base
        self.pid_left = PIDController()
        self.pid_right = PIDController()

        # Current state
        self.target_v = 0.0
        self.target_w = 0.0
        self.actual_v_left = 0.0
        self.actual_v_right = 0.0

    def set_velocity(self, v, w):
        """
        Set target velocity command.

        Args:
            v: Linear velocity (m/s) — positive = forward
            w: Angular velocity (rad/s) — positive = turn left (CCW)
        """
        # Clamp to limits
        v = max(-MAX_LINEAR_VEL, min(MAX_LINEAR_VEL, v))
        w = max(-MAX_ANGULAR_VEL, min(MAX_ANGULAR_VEL, w))
        self.target_v = v
        self.target_w = w

    def get_wheel_velocities(self):
        """
        Convert unicycle (v, w) to differential drive wheel velocities.

        v_left  = v - w * L / 2
        v_right = v + w * L / 2

        where L is the wheel base (distance between wheels).
        """
        v_left = self.target_v - self.target_w * self.wheel_base / 2.0
        v_right = self.target_v + self.target_w * self.wheel_base / 2.0
        return v_left, v_right

    def update(self, actual_v_left, actual_v_right, dt):
        """
        Run PID control loop. Call this at high frequency (50-100Hz).

        Args:
            actual_v_left: Measured left wheel velocity (from encoders)
            actual_v_right: Measured right wheel velocity (from encoders)
            dt: Time step (seconds)

        Returns:
            pwm_left, pwm_right: Motor commands (PWM or voltage signals)
        """
        self.actual_v_left = actual_v_left
        self.actual_v_right = actual_v_right

        target_left, target_right = self.get_wheel_velocities()

        pwm_left = self.pid_left.compute(target_left, actual_v_left, dt)
        pwm_right = self.pid_right.compute(target_right, actual_v_right, dt)

        return pwm_left, pwm_right

    def stop(self):
        """Emergency stop — zero velocity + reset PIDs."""
        self.target_v = 0.0
        self.target_w = 0.0
        self.pid_left.reset()
        self.pid_right.reset()

    def get_odometry(self, v_left, v_right, dt):
        """
        Compute odometry from wheel velocities.
        Returns (dx, dy, dtheta) — motion in robot frame.

        This is the kinematics equation for a differential drive robot.
        """
        v = (v_left + v_right) / 2.0
        w = (v_right - v_left) / self.wheel_base

        if abs(w) < 1e-6:
            # Straight line motion
            dx = v * dt
            dy = 0.0
            dtheta = 0.0
        else:
            # Arc motion
            radius = v / w
            dtheta = w * dt
            dx = radius * math.sin(dtheta)
            dy = radius * (1 - math.cos(dtheta))

        return dx, dy, dtheta
