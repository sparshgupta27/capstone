"""
Rover Brain — Main Entry Point

This is the actual program that runs on the rover (or in simulation).
It initializes all modules, runs the main control loop, and publishes
telemetry to the backend via WebSocket.

Usage:
    python main.py              # Run in simulation mode
    python main.py --real       # Run with real hardware (when available)
"""
import asyncio
import json
import time
import math
import sys
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    BACKEND_WS_URL, SIM_DT, TELEMETRY_PUBLISH_HZ, MAP_PUBLISH_HZ,
    LIDAR_MAX_RANGE,
)
from brain.slam.slam_engine import SLAMEngine
from brain.control.motor_driver import MotorDriver
from brain.perception.sensor_fusion import ExtendedKalmanFilter
from brain.planning.dwa import lidar_to_obstacles
from brain.state_machine.mission_executor import MissionExecutor
from brain.sim.sim_world import SimRobot, SimLiDAR, SimMotors, SimCamera, SimIMU

try:
    import websockets
except ImportError:
    print("ERROR: 'websockets' not installed. Run: pip install websockets")
    sys.exit(1)


class RoverBrain:
    """
    The complete autonomous rover brain.
    Runs the control loop and publishes to the dashboard backend.
    """

    def __init__(self, sim_mode=True):
        self.sim_mode = sim_mode

        # ── Initialize simulation or real hardware ──
        if sim_mode:
            self.robot = SimRobot(x=2.5, y=3.5, theta=0.0)
            self.lidar = SimLiDAR(self.robot)
            self.motors_hw = SimMotors(self.robot)
            self.camera = SimCamera(self.robot)
            self.imu = SimIMU(self.robot)
            print("[BRAIN] Running in SIMULATION mode")
        else:
            # TODO: Initialize real hardware interfaces
            raise NotImplementedError("Real hardware not implemented yet")

        # ── Core algorithms ──
        self.slam = SLAMEngine()
        self.slam.set_pose(2.5, 3.5, 0.0)  # initial known pose

        self.motor_driver = MotorDriver()
        self.ekf = ExtendedKalmanFilter()
        self.ekf.set_pose(2.5, 3.5, 0.0)

        self.mission = MissionExecutor(self.slam, self.motor_driver, self.ekf)

        # ── Timing ──
        self.dt = SIM_DT
        self.tick_count = 0
        self.odom_publish_interval = 1.0 / TELEMETRY_PUBLISH_HZ
        self.map_publish_interval = 1.0 / MAP_PUBLISH_HZ
        self.last_odom_publish = 0
        self.last_map_publish = 0

        # ── WebSocket ──
        self.ws = None
        self.running = True

    async def connect_backend(self):
        """Connect to the backend WebSocket server."""
        url = BACKEND_WS_URL + "?role=publisher"
        while self.running:
            try:
                print(f"[BRAIN] Connecting to backend at {BACKEND_WS_URL}...")
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    print("[BRAIN] Connected to backend!")

                    # Start the brain
                    self.mission.start_mission()

                    # Run control loop and listen for commands concurrently
                    await asyncio.gather(
                        self.control_loop(),
                        self.listen_for_commands(ws),
                    )
            except (ConnectionRefusedError, OSError) as e:
                print(f"[BRAIN] Backend not available: {e}. Retrying in 3s...")
                await asyncio.sleep(3)
            except websockets.exceptions.ConnectionClosed:
                print("[BRAIN] Connection lost. Reconnecting...")
                self.ws = None
                await asyncio.sleep(2)

    async def control_loop(self):
        """
        Main control loop — runs at ~50Hz.

        Each iteration:
        1. Read sensors
        2. Run SLAM (scan match + map update)
        3. Run EKF (sensor fusion)
        4. Run mission executor (state machine + planning)
        5. Send motor commands
        6. Publish telemetry
        """
        print("[BRAIN] Control loop started at {:.0f}Hz".format(1.0 / self.dt))

        while self.running:
            loop_start = time.time()
            self.tick_count += 1

            # ── 1. Read sensors ──
            lidar_scan = self.lidar.get_scan()
            v_left, v_right = self.motors_hw.get_encoder_velocities()
            _, _, imu_yaw = self.imu.get_orientation()

            # ── 2. Compute odometry from wheel encoders ──
            odom_dx, odom_dy, odom_dtheta = self.motor_driver.get_odometry(
                v_left, v_right, self.dt
            )

            # ── 3. Run SLAM ──
            slam_pose = self.slam.update(lidar_scan, odom_dx, odom_dy, odom_dtheta)

            # ── 4. Run EKF ──
            v = (v_left + v_right) / 2.0
            w = (v_right - v_left) / self.motor_driver.wheel_base
            self.ekf.predict(v, w, self.dt)
            self.ekf.update(slam_pose[0], slam_pose[1], slam_pose[2])
            fused_pose = self.ekf.get_pose()

            # ── 5. Convert LiDAR to obstacle points ──
            obstacle_points = lidar_to_obstacles(
                fused_pose[0], fused_pose[1], fused_pose[2],
                lidar_scan, LIDAR_MAX_RANGE
            )

            # ── 6. Run mission executor (state machine + planning) ──
            battery = self.robot.battery if self.sim_mode else 100.0
            cmd_v, cmd_w, mission_info = self.mission.tick(
                lidar_scan, battery, obstacle_points
            )

            # ── 7. Send motor commands ──
            self.motor_driver.set_velocity(cmd_v, cmd_w)
            target_vl, target_vr = self.motor_driver.get_wheel_velocities()
            self.motors_hw.set_speeds(target_vl, target_vr)

            # ── 8. Step simulation ──
            if self.sim_mode:
                self.robot.step(self.dt)

            # ── 9. Object detection ──
            if self.sim_mode:
                detections = self.camera.detect_objects()
                for det in detections:
                    self.mission.add_detection(det)
                    await self._publish('detection', det)
                    print(f"[DETECT] {det['label']} ({det['confidence']:.0%}) at ({det['world_pos']['x']:.1f}, {det['world_pos']['y']:.1f})")

            # ── 10. Publish telemetry ──
            now = time.time()
            if now - self.last_odom_publish >= self.odom_publish_interval:
                await self._publish_odom(fused_pose, cmd_v, cmd_w)
                await self._publish_battery(battery)
                await self._publish_status(mission_info['state'], abs(cmd_v))
                self.last_odom_publish = now

            if now - self.last_map_publish >= self.map_publish_interval:
                await self._publish_map()
                self.last_map_publish = now

            # ── Timing ──
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.dt - elapsed)
            await asyncio.sleep(sleep_time)

    async def listen_for_commands(self, ws):
        """Listen for commands from the dashboard via backend."""
        try:
            async for message in ws:
                payload = json.loads(message)
                event = payload.get('event', '')
                data = payload.get('data', {})

                if event == 'new_waypoint':
                    x, y = data.get('x', 0), data.get('y', 0)
                    self.mission.add_user_waypoint(x, y)
                    print(f"[BRAIN] Waypoint received: ({x:.1f}, {y:.1f})")

                elif event == 'mission_start':
                    self.mission.start_mission()

                elif event == 'mission_stop':
                    self.mission.stop_mission()

                elif event == 'mission_pause':
                    self.mission.stop_mission()

        except websockets.exceptions.ConnectionClosed:
            pass

    # ── Publishing helpers ──────────────────────────────────────

    async def _publish(self, msg_type, data):
        """Send a message to the backend."""
        if self.ws:
            try:
                payload = {**data, 'type': msg_type, 'timestamp': time.time() * 1000}
                await self.ws.send(json.dumps(payload))
            except Exception:
                pass

    async def _publish_odom(self, pose, v, w):
        await self._publish('odom', {
            'x': round(pose[0], 4),
            'y': round(pose[1], 4),
            'theta': round(pose[2], 4),
            'vx': round(v, 4),
            'vtheta': round(w, 4),
        })

    async def _publish_battery(self, level):
        await self._publish('battery', {
            'level': round(level, 1),
            'charging': False,
        })

    async def _publish_status(self, state, speed):
        await self._publish('status', {
            'state': state,
            'speed': round(speed, 3),
        })

    async def _publish_map(self):
        map_dict = self.slam.get_map_dict()
        map_dict['timestamp'] = time.time() * 1000
        if self.ws:
            try:
                await self.ws.send(json.dumps(map_dict))
            except Exception:
                pass


async def main():
    print("=" * 60)
    print("  AUTONOMOUS ROVER BRAIN")
    print("  SLAM | Path Planning | Obstacle Avoidance | EKF")
    print("=" * 60)

    sim_mode = '--real' not in sys.argv
    brain = RoverBrain(sim_mode=sim_mode)
    await brain.connect_backend()


if __name__ == '__main__':
    asyncio.run(main())
