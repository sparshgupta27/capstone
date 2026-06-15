# 🤖 Autonomous Rover Monitoring System

Real-time autonomous rover monitoring with simulated telemetry, SLAM-like mapping, object detection, and an interactive React dashboard.

## Architecture

```
Mock Publisher (Python) → WebSocket → Backend (Node.js/Express) → WebSocket → React Dashboard
                                           ↕
                                       MongoDB
```

## Quick Start

### 1. Start the Backend
```bash
cd backend
npm install
npm run dev
```
The server runs on `http://localhost:5000` (HTTP + WebSocket).

### 2. Start the Mock Publisher
```bash
cd mock-publisher
pip install websockets
python publisher.py
```
This simulates a rover with LiDAR, odometry, and object detection.

### 3. Start the Dashboard
```bash
cd dashboard
npm install
npm run dev
```
Open `http://localhost:5173` to see the live dashboard.

### Optional: MongoDB
Install MongoDB locally or use a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster.
Update `backend/.env` with your connection string.

> **Note:** The system works without MongoDB — data just won't be persisted for historical queries.

## Features

- 🗺️ **Live Map** — Occupancy grid + robot position + path trail, updated in real time
- 🎯 **Object Detection** — Simulated YOLO detections with confidence scores
- 📍 **Waypoint Navigation** — Click on the map to set navigation waypoints
- 📊 **Telemetry Dashboard** — Battery, speed, heading, connection status
- 📈 **Real-time Charts** — Speed, battery, and detection rate sparklines
- 🚀 **Mission Control** — Start, pause, and stop exploration missions

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Node.js, Express, WebSocket (`ws`), Mongoose |
| Database | MongoDB |
| Dashboard | React 18, Vite, HTML5 Canvas |
| Publisher | Python, asyncio, websockets |

## Project Structure

```
capstone/
├── backend/          # Node.js WebSocket hub + REST API
├── mock-publisher/   # Python rover simulator
├── dashboard/        # React real-time dashboard
└── README.md
```
