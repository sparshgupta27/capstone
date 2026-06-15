"""
PID Controller — Proportional-Integral-Derivative control for motor velocity tracking.

On a real rover, this converts target wheel velocities into PWM signals for motors.
The PID loop runs at a high frequency (50-100Hz) to maintain smooth motion.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import PID_KP, PID_KI, PID_KD, PID_MAX_OUTPUT, PID_INTEGRAL_LIMIT


class PIDController:
    """
    Standard PID controller with anti-windup.
    One instance per wheel (left and right).
    """

    def __init__(self, kp=PID_KP, ki=PID_KI, kd=PID_KD,
                 max_output=PID_MAX_OUTPUT, integral_limit=PID_INTEGRAL_LIMIT):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_output = max_output
        self.integral_limit = integral_limit

        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None

    def compute(self, target, actual, dt):
        """
        Compute PID output.

        Args:
            target: Desired velocity (m/s or rad/s)
            actual: Measured velocity
            dt: Time since last call (seconds)

        Returns:
            output: Control signal (e.g., PWM value or motor command)
        """
        if dt <= 0:
            return 0.0

        error = target - actual

        # Proportional
        p_term = self.kp * error

        # Integral with anti-windup
        self.integral += error * dt
        self.integral = max(-self.integral_limit, min(self.integral_limit, self.integral))
        i_term = self.ki * self.integral

        # Derivative
        d_term = self.kd * (error - self.prev_error) / dt
        self.prev_error = error

        # Combined output
        output = p_term + i_term + d_term

        # Clamp output
        output = max(-self.max_output, min(self.max_output, output))

        return output

    def reset(self):
        """Reset the controller state."""
        self.integral = 0.0
        self.prev_error = 0.0
