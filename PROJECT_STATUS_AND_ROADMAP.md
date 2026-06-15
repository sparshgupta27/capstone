# Autonomous Rover Project: Status and Roadmap

## 1. Project Overview

This project is an autonomous rover monitoring and navigation prototype. It currently provides a complete simulation pipeline:

```text
Simulated Rover / Rover Brain
          |
          | WebSocket telemetry and commands
          v
Node.js Backend
          |
          | WebSocket updates
          v
React Monitoring Dashboard
```

The project demonstrates the software concepts required for an autonomous indoor rover, including mapping, localization, path planning, obstacle avoidance, telemetry, object detection, and mission control.

The rover currently runs in simulation. Physical robot control and ROS 2 integration have not yet been implemented.

## 2. Current Project Components

### 2.1 Rover Brain

Location: `brain/`

The rover brain is the main autonomous control program. It includes:

- A 50 Hz robot control loop
- Differential-drive motor command generation
- Wheel-encoder odometry calculations
- Simulated LiDAR, IMU, camera, motors, and robot physics
- Occupancy-grid mapping
- ICP-based scan matching
- Extended Kalman Filter sensor fusion
- A* global path planning
- Dynamic Window Approach local obstacle avoidance
- Frontier-based autonomous exploration
- Mission state management
- Battery-level monitoring and emergency-stop state
- User waypoint handling
- Object detection simulation
- WebSocket telemetry publishing

The following command is intended to run the simulated autonomous brain:

```powershell
py brain\main.py
```

The real-hardware mode is declared but not implemented:

```powershell
py brain\main.py --real
```

### 2.2 Mock Rover Publisher

Location: `mock-publisher/`

The mock publisher is a simpler dashboard demonstration tool. It includes:

- Simulated robot movement
- Simulated LiDAR scans
- Simulated occupancy-grid generation
- Simulated object detections
- Battery and status telemetry
- WebSocket communication
- Basic waypoint and mission-command handling

It can be used when testing the dashboard without running the full autonomous brain:

```powershell
cd mock-publisher
py publisher.py
```

The mock publisher and full rover brain should not run at the same time because both act as rover telemetry publishers.

### 2.3 Backend

Location: `backend/`

The Node.js backend acts as the communication hub between the rover and dashboard. It includes:

- Express HTTP server
- WebSocket server
- Dashboard and publisher connection roles
- Live telemetry forwarding
- Mission-control command forwarding
- Waypoint command forwarding
- Latest-state storage in memory
- Optional MongoDB persistence
- REST API routes for telemetry, detections, missions, and waypoints
- Health-check endpoint

Start the backend with:

```powershell
cd backend
npm.cmd run dev
```

The backend can operate without MongoDB for live WebSocket communication, but some REST endpoints currently fail when MongoDB is unavailable.

### 2.4 Monitoring Dashboard

Location: `dashboard/`

The React dashboard includes:

- Live robot position and heading display
- Occupancy-grid map display
- Robot path trail
- Floor-plan wall display
- Object-detection markers and feed
- Battery, speed, heading, and connection status
- Mission start, pause, and stop controls
- Click-to-create waypoint controls
- Waypoint list and cancellation controls
- Live speed, battery, and detection charts
- Automatic WebSocket reconnection

Start the dashboard with:

```powershell
cd dashboard
npm.cmd run dev
```

The dashboard is available at:

```text
http://localhost:5173
```

## 3. What Currently Works

- The dashboard production build completes successfully.
- The backend starts and its health endpoint works.
- The dashboard connects to the backend through WebSockets.
- The mock publisher can produce live dashboard telemetry.
- The rover brain contains a complete simulation control pipeline.
- Live robot pose, battery, status, detections, and maps can be displayed.
- Dashboard mission commands are forwarded to connected publishers.
- Dashboard map clicks generate waypoint commands.
- MongoDB persistence is optional for live dashboard operation.

## 4. Known Issues and Limitations

### 4.1 Mission and Waypoint Behavior

- Cancelling a waypoint on the dashboard does not currently cancel navigation on the rover.
- A dashboard waypoint does not immediately interrupt autonomous exploration.
- The mock rover may continue moving after mission stop or pause.
- Unreachable exploration frontiers may be repeatedly selected.
- Waypoints may be duplicated on the dashboard after WebSocket reconnection.
- The rover does not report waypoint reached or failed states back to the backend.

### 4.2 Backend and API

- `/api/grid/latest` is documented but not implemented.
- Some REST endpoints return errors when MongoDB is unavailable.
- WebSocket messages are not validated before use.
- There is no authentication or authorization.
- There is no support for selecting between multiple robots.
- Mission and waypoint state is not fully synchronized between the rover, backend, and dashboard.

### 4.3 Dashboard

- Dashboard linting currently reports React hook errors and a warning.
- Mission state is based mainly on backend commands instead of confirmed rover state.
- The reset-view map button does not perform an action.
- There is no manual driving or emergency-stop control.
- There is no camera-video display.
- There is no interface for configuring robot parameters.

### 4.4 Rover Brain and Simulation

- Real hardware mode raises `NotImplementedError`.
- Simulated object detection does not use an actual camera or machine-learning model.
- The educational SLAM and navigation implementations are not ready for safety-critical physical operation.
- The IMU reading is created but not currently fused into the EKF.
- There are no automated tests for mapping, navigation, backend commands, or dashboard behavior.
- Python dependencies and supported Python version are not fully documented for the rover brain.

## 5. ROS 2 Status

ROS and ROS 2 are not currently used by the project. The rover brain communicates directly with the Node.js backend through WebSockets.

For a physical robot, ROS 2 should be added to provide reliable hardware integration, transforms, localization, mapping, and navigation.

Recommended ROS 2 architecture:

```text
LiDAR Driver ----------> /scan ----------> slam_toolbox
Wheel Encoders --------> /wheel/odom ----\
IMU -------------------> /imu/data -------+--> robot_localization --> /odom
slam_toolbox ----------> /map
Nav2 ------------------> /cmd_vel --------> ros2_control --> Motors
Camera Driver ---------> /camera/image_raw --> Object Detection
ROS Dashboard Bridge --> WebSocket Backend --> React Dashboard
```

Required coordinate frames:

```text
map -> odom -> base_link -> lidar_link
                         -> camera_link
                         -> imu_link
```

## 6. Work Required for a Physical Robot

### Phase 1: Stabilize the Current Prototype

- Fix waypoint cancellation and mission stop/pause behavior.
- Make user waypoints immediately take navigation priority.
- Prevent repeated selection of unreachable frontiers.
- Remove duplicate waypoints after dashboard reconnection.
- Fix dashboard lint errors.
- Make database-optional REST endpoints work correctly.
- Add structured message validation.
- Add automated tests.
- Document all installation and startup commands.

### Phase 2: Define the Robot Hardware

Select and document:

- Compute platform, such as Raspberry Pi 5 or NVIDIA Jetson
- Motor driver and supported voltage/current
- Motors and wheel encoders
- LiDAR model
- IMU model
- Camera model
- Battery, regulator, and power-distribution design
- Chassis dimensions, wheel radius, and wheel separation
- Physical emergency-stop button

### Phase 3: Add ROS 2

Recommended base platform:

- Ubuntu 24.04
- ROS 2 Jazzy

Required ROS 2 work:

- Create a ROS 2 workspace and rover packages.
- Create the rover URDF/Xacro model.
- Publish correct static and dynamic TF transforms.
- Configure `ros2_control` for motors and encoders.
- Add LiDAR, IMU, and camera drivers.
- Configure `robot_localization`.
- Configure `slam_toolbox`.
- Configure Nav2.
- Add launch files and parameter files.
- Add a WebSocket bridge between ROS 2 topics and the existing backend.

### Phase 4: Hardware Drivers and Control

- Implement motor output and encoder input.
- Calibrate wheel radius and wheel separation.
- Verify odometry direction and scale.
- Add motor acceleration limits.
- Implement a hardware emergency stop.
- Add watchdog behavior that stops motors if commands are lost.
- Add battery-voltage monitoring.

### Phase 5: Perception

- Connect a real camera.
- Choose an object-detection model.
- Run object detection on the rover or an external computer.
- Publish detections with timestamps and coordinate frames.
- Transform detections into map coordinates.
- Track and deduplicate detected objects.

### Phase 6: Testing and Safety

- Unit-test planning, mapping, and command handling.
- Add integration tests for rover-to-backend-to-dashboard communication.
- Test motor direction with wheels raised.
- Test emergency-stop behavior.
- Test command-loss and network-loss behavior.
- Test mapping and navigation at low speed.
- Validate obstacle-clearance distances.
- Record ROS bags for repeatable testing.
- Add logs, diagnostics, and performance monitoring.

## 7. Recommended Final System Responsibilities

For the final physical rover, responsibilities should be divided as follows:

### ROS 2 Rover Computer

- Hardware drivers
- Motor control
- Sensor processing
- TF transforms
- Localization
- SLAM
- Navigation
- Safety watchdog
- Object detection

### Node.js Backend

- Remote monitoring gateway
- User and mission management
- Historical data storage
- WebSocket bridge for the dashboard
- Authentication and access control

### React Dashboard

- Live map and telemetry
- Mission creation and monitoring
- Waypoint submission
- Detection review
- Manual control when permitted
- Emergency-stop request
- System diagnostics

## 8. Suggested Priority Order

1. Fix current mission, waypoint, and dashboard issues.
2. Add tests and complete setup documentation.
3. Finalize the physical hardware list.
4. Create the ROS 2 workspace, URDF, and TF tree.
5. Implement motor and encoder control with `ros2_control`.
6. Integrate LiDAR, IMU, localization, and SLAM.
7. Configure Nav2 and validate navigation.
8. Build the ROS-to-dashboard bridge.
9. Add real camera object detection.
10. Complete safety testing and field validation.

## 9. Current Completion Summary

The project is currently a strong autonomous-rover software simulation and monitoring prototype. It demonstrates most of the major concepts required by the final system and provides a useful dashboard and backend foundation.

It is not yet ready to operate a physical robot. The major remaining work is ROS 2 integration, hardware-driver implementation, navigation-system configuration, safety controls, testing, and physical validation.
