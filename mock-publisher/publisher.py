"""
Mock Telemetry Publisher — connects to the backend WebSocket server and
publishes simulated rover telemetry at realistic rates.

Usage:
    python publisher.py
    python publisher.py --url ws://localhost:5000
"""
import asyncio
import json
import time
import random
import sys
import io

# Fix Windows console encoding for emoji/unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import websockets
except ImportError:
    print("❌ 'websockets' package not found. Install with: pip install websockets")
    sys.exit(1)

from simulator import Robot, scan_lidar, simulate_detection, build_occupancy_grid, CONFIG

WS_URL = CONFIG.get('websocket_url', 'ws://localhost:5000')
RATES = CONFIG['publish_rates']


class Publisher:
    def __init__(self, url):
        self.url = url + '?role=publisher'
        self.robot = Robot()
        self.ws = None
        self.running = True
        self.last_sim_time = time.time()

    async def connect(self):
        """Connect to backend WebSocket with auto-retry"""
        while self.running:
            try:
                print(f"🔌 Connecting to {self.url}...")
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    print(f"✅ Connected to backend!")
                    await self.run(ws)
            except (ConnectionRefusedError, OSError) as e:
                print(f"⚠️  Connection failed: {e}. Retrying in 3s...")
                await asyncio.sleep(3)
            except websockets.exceptions.ConnectionClosed:
                print(f"⚠️  Connection closed. Reconnecting in 2s...")
                await asyncio.sleep(2)

    async def run(self, ws):
        """Main loop — schedule all publishers concurrently"""
        # Listen for incoming commands (waypoints, mission control)
        recv_task = asyncio.create_task(self.receive_commands(ws))

        # Publisher tasks at different rates
        tasks = [
            asyncio.create_task(self.publish_odometry(ws)),
            asyncio.create_task(self.publish_lidar(ws)),
            asyncio.create_task(self.publish_detections(ws)),
            asyncio.create_task(self.publish_battery(ws)),
            asyncio.create_task(self.publish_status(ws)),
            asyncio.create_task(self.publish_grid(ws)),
            asyncio.create_task(self.simulate_loop()),
            recv_task,
        ]

        try:
            await asyncio.gather(*tasks)
        except websockets.exceptions.ConnectionClosed:
            for t in tasks:
                t.cancel()
            raise

    async def simulate_loop(self):
        """Update robot physics at 50Hz"""
        while self.running:
            now = time.time()
            dt = now - self.last_sim_time
            self.last_sim_time = now
            self.robot.update(dt)
            await asyncio.sleep(0.02)  # 50 Hz

    async def publish_odometry(self, ws):
        """Publish odometry at configured rate"""
        interval = 1.0 / RATES['odometry_hz']
        while self.running:
            data = self.robot.get_odom()
            await ws.send(json.dumps(data))
            await asyncio.sleep(interval)

    async def publish_lidar(self, ws):
        """Publish LiDAR scans at configured rate"""
        interval = 1.0 / RATES['lidar_hz']
        while self.running:
            data = scan_lidar(self.robot)
            await ws.send(json.dumps(data))
            await asyncio.sleep(interval)

    async def publish_detections(self, ws):
        """Publish random detections at random intervals"""
        min_interval, max_interval = RATES['detection_interval_s']
        while self.running:
            interval = random.uniform(min_interval, max_interval)
            await asyncio.sleep(interval)
            data = simulate_detection(self.robot)
            await ws.send(json.dumps(data))
            print(f"🎯 Detected: {data['label']} ({data['confidence']:.0%}) at ({data['world_pos']['x']:.1f}, {data['world_pos']['y']:.1f})")

    async def publish_battery(self, ws):
        """Publish battery status at configured rate"""
        interval = 1.0 / RATES['battery_hz']
        while self.running:
            data = self.robot.get_battery()
            await ws.send(json.dumps(data))
            await asyncio.sleep(interval)

    async def publish_status(self, ws):
        """Publish robot status at configured rate"""
        interval = 1.0 / RATES['status_hz']
        while self.running:
            data = self.robot.get_status()
            await ws.send(json.dumps(data))
            await asyncio.sleep(interval)

    async def publish_grid(self, ws):
        """Publish occupancy grid at configured rate"""
        interval = 1.0 / RATES['grid_hz']
        while self.running:
            data = build_occupancy_grid(self.robot)
            await ws.send(json.dumps(data))
            await asyncio.sleep(interval)

    async def receive_commands(self, ws):
        """Listen for commands from backend (waypoints, mission control)"""
        async for message in ws:
            try:
                payload = json.loads(message)
                event = payload.get('event', '')
                data = payload.get('data', {})

                if event == 'new_waypoint':
                    print(f"📍 New waypoint received: ({data.get('x', 0):.1f}, {data.get('y', 0):.1f}) — navigating...")
                    self.robot.target = (data.get('x', self.robot.x), data.get('y', self.robot.y))
                elif event == 'mission_start':
                    print("🚀 Mission started!")
                    self.robot.state = 'exploring'
                elif event == 'mission_stop':
                    print("🛑 Mission stopped.")
                    self.robot.state = 'idle'
                elif event == 'mission_pause':
                    print("⏸️  Mission paused.")
                    self.robot.state = 'idle'
                else:
                    print(f"📩 Unknown command: {event}")
            except json.JSONDecodeError:
                pass


async def main():
    url = WS_URL
    # Allow override from command line
    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        if idx + 1 < len(sys.argv):
            url = sys.argv[idx + 1]

    print("=" * 50)
    print("🤖 Rover Mock Telemetry Publisher")
    print(f"   Backend: {url}")
    print(f"   Odometry: {RATES['odometry_hz']}Hz")
    print(f"   LiDAR:    {RATES['lidar_hz']}Hz ({CONFIG['lidar']['num_rays']} rays)")
    print(f"   Grid:     {RATES['grid_hz']}Hz")
    print(f"   Floor:    {FLOOR_W}m × {FLOOR_H}m")
    print("=" * 50)

    publisher = Publisher(url)
    await publisher.connect()

FLOOR_W = CONFIG['floor_plan']['width']
FLOOR_H = CONFIG['floor_plan']['height']

if __name__ == '__main__':
    asyncio.run(main())
