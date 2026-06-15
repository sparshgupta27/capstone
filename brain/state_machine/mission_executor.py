"""
Mission Executor — Finite State Machine coordinating all brain modules.

States:
  IDLE → EXPLORING → NAVIGATING → EXPLORING → ... → MISSION_COMPLETE
                  ↓
           OBSTACLE_AVOIDANCE
                  ↓
              NAVIGATING
                  ↓
           EMERGENCY_STOP (battery critical)

The state machine is the "decision maker" — it decides WHAT to do.
The planners and controllers decide HOW to do it.
"""
import math
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    WAYPOINT_REACHED_THRESHOLD, BATTERY_CRITICAL_LEVEL, STUCK_TIMEOUT,
    MAX_LINEAR_VEL, SIM_DT,
)


class RoverState:
    IDLE = 'idle'
    EXPLORING = 'exploring'
    NAVIGATING = 'navigating'
    OBSTACLE_AVOIDANCE = 'obstacle_avoidance'
    MISSION_COMPLETE = 'mission_complete'
    EMERGENCY_STOP = 'emergency_stop'
    NAVIGATING_TO_WAYPOINT = 'navigating_to_waypoint'


class MissionExecutor:
    """
    FSM that coordinates the autonomous rover operation.

    Each tick:
    1. Read sensors
    2. Update SLAM
    3. Make a state-based decision
    4. Execute the decision (plan path, avoid obstacle, etc.)
    5. Send motor commands
    """

    def __init__(self, slam_engine, motor_driver, ekf):
        self.slam = slam_engine
        self.motors = motor_driver
        self.ekf = ekf

        self.state = RoverState.IDLE
        self.current_target = None       # (x, y) world coordinates
        self.current_path = []           # list of (x, y) waypoints
        self.path_index = 0              # current waypoint index in path
        self.user_waypoints = []         # waypoints set by the user
        self.detected_objects = []       # accumulated detections

        # Stuck detection
        self.last_pose = None
        self.stuck_timer = 0.0
        self.mission_start_time = None
        self.exploration_targets_tried = set()

    def get_state(self):
        return self.state

    def start_mission(self):
        """Start autonomous exploration mission."""
        self.state = RoverState.EXPLORING
        self.mission_start_time = time.time()
        self.exploration_targets_tried.clear()
        print("[MISSION] Mission started — entering EXPLORING state")

    def stop_mission(self):
        """Stop the current mission."""
        self.state = RoverState.IDLE
        self.motors.stop()
        self.current_target = None
        self.current_path = []
        print("[MISSION] Mission stopped")

    def add_user_waypoint(self, x, y):
        """Add a user-defined waypoint for navigation."""
        self.user_waypoints.append((x, y))
        print(f"[MISSION] User waypoint added: ({x:.1f}, {y:.1f})")

        # If idle, start navigating to it
        if self.state == RoverState.IDLE:
            self.state = RoverState.NAVIGATING_TO_WAYPOINT

    def tick(self, lidar_scan, battery_level, obstacle_points):
        """
        Main decision loop — call this every control cycle.

        Args:
            lidar_scan: Current LiDAR scan (list of ranges)
            battery_level: Battery percentage (0-100)
            obstacle_points: Nearby obstacles in world coordinates

        Returns:
            v, w: Velocity commands for the motor controller
            info: Dict with debug info for the dashboard
        """
        pose = self.ekf.get_pose()
        x, y, theta = pose

        info = {
            'state': self.state,
            'target': self.current_target,
            'path_length': len(self.current_path),
            'detections': len(self.detected_objects),
        }

        # ── Emergency stop check ──
        if battery_level < BATTERY_CRITICAL_LEVEL and self.state not in [RoverState.IDLE, RoverState.EMERGENCY_STOP]:
            self.state = RoverState.EMERGENCY_STOP
            self.motors.stop()
            print(f"[MISSION] ⚠️ EMERGENCY STOP — battery at {battery_level:.0f}%")
            return 0.0, 0.0, info

        # ── Stuck detection ──
        if self.last_pose:
            dist_moved = math.sqrt((x - self.last_pose[0])**2 + (y - self.last_pose[1])**2)
            if dist_moved < 0.01 and self.state in [RoverState.NAVIGATING, RoverState.EXPLORING]:
                self.stuck_timer += SIM_DT
                if self.stuck_timer > STUCK_TIMEOUT:
                    print("[MISSION] Stuck detected — re-planning")
                    self.current_path = []
                    self.current_target = None
                    self.stuck_timer = 0
                    if self.state == RoverState.NAVIGATING:
                        self.state = RoverState.EXPLORING
            else:
                self.stuck_timer = 0
        self.last_pose = (x, y)

        # ── State machine ──
        if self.state == RoverState.IDLE:
            return 0.0, 0.0, info

        elif self.state == RoverState.EMERGENCY_STOP:
            return 0.0, 0.0, info

        elif self.state == RoverState.MISSION_COMPLETE:
            return 0.0, 0.0, info

        elif self.state == RoverState.NAVIGATING_TO_WAYPOINT:
            return self._handle_user_waypoint(pose, obstacle_points, info)

        elif self.state == RoverState.EXPLORING:
            return self._handle_exploring(pose, obstacle_points, info)

        elif self.state == RoverState.NAVIGATING:
            return self._handle_navigating(pose, obstacle_points, info)

        return 0.0, 0.0, info

    def _handle_exploring(self, pose, obstacle_points, info):
        """Find and navigate to the next frontier."""
        from brain.planning.frontier import select_best_frontier
        from brain.planning.astar import plan_path

        x, y, theta = pose

        # If we don't have a target, find one
        if self.current_target is None or not self.current_path:
            target = select_best_frontier(self.slam.get_map(), x, y)

            if target is None:
                # Check user waypoints
                if self.user_waypoints:
                    self.state = RoverState.NAVIGATING_TO_WAYPOINT
                    return 0.0, 0.0, info

                self.state = RoverState.MISSION_COMPLETE
                print("[MISSION] ✅ Exploration complete — no more frontiers!")
                return 0.0, 0.0, info

            self.current_target = target
            self.current_path = plan_path(self.slam.get_map(), (x, y), target)
            self.path_index = 0

            if not self.current_path:
                # Can't reach this frontier, try another
                self.current_target = None
                return 0.0, 0.0, info

            print(f"[MISSION] Exploring toward ({target[0]:.1f}, {target[1]:.1f})")

        # Follow path
        return self._follow_path(pose, obstacle_points, info)

    def _handle_navigating(self, pose, obstacle_points, info):
        """Navigate along the current path."""
        if not self.current_path:
            self.state = RoverState.EXPLORING
            return 0.0, 0.0, info

        return self._follow_path(pose, obstacle_points, info)

    def _handle_user_waypoint(self, pose, obstacle_points, info):
        """Navigate to a user-defined waypoint."""
        from brain.planning.astar import plan_path

        x, y, theta = pose

        if not self.user_waypoints:
            self.state = RoverState.EXPLORING if self.mission_start_time else RoverState.IDLE
            return 0.0, 0.0, info

        # Plan path to next user waypoint
        if not self.current_path:
            target = self.user_waypoints[0]
            self.current_target = target
            self.current_path = plan_path(self.slam.get_map(), (x, y), target)
            self.path_index = 0

            if not self.current_path:
                print(f"[MISSION] Cannot reach waypoint ({target[0]:.1f}, {target[1]:.1f}) — skipping")
                self.user_waypoints.pop(0)
                return 0.0, 0.0, info

        v, w, info = self._follow_path(pose, obstacle_points, info)

        # Check if we reached the waypoint
        if self.current_target:
            dist = math.sqrt((x - self.current_target[0])**2 + (y - self.current_target[1])**2)
            if dist < WAYPOINT_REACHED_THRESHOLD:
                print(f"[MISSION] 📍 Waypoint reached: ({self.current_target[0]:.1f}, {self.current_target[1]:.1f})")
                if self.user_waypoints:
                    self.user_waypoints.pop(0)
                self.current_target = None
                self.current_path = []

        return v, w, info

    def _follow_path(self, pose, obstacle_points, info):
        """Follow the current path using DWA for local obstacle avoidance."""
        from brain.planning.dwa import dwa_control

        x, y, theta = pose

        # Get next waypoint on path
        while self.path_index < len(self.current_path):
            wx, wy = self.current_path[self.path_index]
            dist = math.sqrt((x - wx)**2 + (y - wy)**2)
            if dist < WAYPOINT_REACHED_THRESHOLD:
                self.path_index += 1
            else:
                break

        # Check if path is complete
        if self.path_index >= len(self.current_path):
            self.current_path = []
            self.current_target = None
            if self.state == RoverState.NAVIGATING:
                self.state = RoverState.EXPLORING
            return 0.0, 0.0, info

        # Use DWA for local planning toward the next waypoint
        goal = self.current_path[min(self.path_index + 2, len(self.current_path) - 1)]
        v, w, traj = dwa_control(
            [x, y, theta],
            [self.motors.target_v, self.motors.target_w],
            goal,
            obstacle_points
        )

        info['local_goal'] = goal
        return v, w, info

    def add_detection(self, detection):
        """Record a detected object."""
        self.detected_objects.append(detection)
