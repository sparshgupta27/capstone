"""
Hardware Abstraction Layer — Abstract interfaces for all sensors and actuators.

Each interface has two implementations:
  1. Simulated (in sim/) — for testing without hardware
  2. Real (add later) — for actual RPLiDAR, GPIO motors, USB camera, etc.

The brain code ONLY uses these interfaces, never touches hardware directly.
This means swapping from simulation to real hardware requires ZERO brain code changes.
"""
from abc import ABC, abstractmethod


class LiDARInterface(ABC):
    """Abstract LiDAR sensor interface."""

    @abstractmethod
    def get_scan(self):
        """
        Get a single LiDAR scan.
        Returns: List of range values in meters (360 values for 360° scan)
        """
        pass

    @abstractmethod
    def get_num_rays(self):
        """Number of rays per scan."""
        pass


class MotorInterface(ABC):
    """Abstract motor interface for differential drive."""

    @abstractmethod
    def set_speeds(self, left_speed, right_speed):
        """
        Set wheel speeds.
        Args:
            left_speed: Left wheel velocity (m/s or PWM)
            right_speed: Right wheel velocity (m/s or PWM)
        """
        pass

    @abstractmethod
    def get_encoder_velocities(self):
        """
        Read wheel velocities from encoders.
        Returns: (left_velocity, right_velocity) in m/s
        """
        pass

    @abstractmethod
    def stop(self):
        """Emergency stop."""
        pass


class CameraInterface(ABC):
    """Abstract camera interface."""

    @abstractmethod
    def get_frame(self):
        """
        Capture a camera frame.
        Returns: Image data (format depends on implementation)
        """
        pass


class IMUInterface(ABC):
    """Abstract IMU interface."""

    @abstractmethod
    def get_orientation(self):
        """
        Get current orientation.
        Returns: (roll, pitch, yaw) in radians
        """
        pass

    @abstractmethod
    def get_angular_velocity(self):
        """
        Get angular velocity.
        Returns: (wx, wy, wz) in rad/s
        """
        pass
