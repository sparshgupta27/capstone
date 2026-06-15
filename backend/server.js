import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';

import connectDB from './config/db.js';
import logger from './utils/logger.js';
import { setupWebSocket, getClientCounts } from './ws/handler.js';

import telemetryRoutes from './routes/telemetry.js';
import detectionsRoutes from './routes/detections.js';
import waypointsRoutes from './routes/waypoints.js';
import missionsRoutes from './routes/missions.js';

const PORT = process.env.PORT || 5000;
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// REST API routes
app.use('/api/telemetry', telemetryRoutes);
app.use('/api/detections', detectionsRoutes);
app.use('/api/waypoints', waypointsRoutes);
app.use('/api/missions', missionsRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  const counts = getClientCounts();
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    connections: counts,
    timestamp: new Date().toISOString(),
  });
});

// API overview
app.get('/api', (req, res) => {
  res.json({
    name: 'Rover Backend API',
    version: '1.0.0',
    endpoints: {
      'GET /api/health': 'Health check',
      'GET /api/telemetry': 'Historical pose data',
      'GET /api/telemetry/latest': 'Most recent pose',
      'GET /api/detections': 'Detection history',
      'GET /api/detections/stats': 'Detection stats by label',
      'GET /api/grid/latest': 'Latest occupancy grid',
      'GET|POST /api/waypoints': 'List / create waypoints',
      'PATCH|DELETE /api/waypoints/:id': 'Update / delete waypoint',
      'GET|POST /api/missions': 'List / create missions',
      'GET|PATCH /api/missions/:id': 'Get / update mission',
      'GET /api/missions/:id/stats': 'Mission statistics',
    },
    websocket: {
      url: `ws://localhost:${PORT}`,
      roles: {
        publisher: 'Connect as ?role=publisher to send telemetry',
        dashboard: 'Connect as ?role=dashboard to receive updates',
      },
    },
  });
});

// Create HTTP server and attach WebSocket
const server = createServer(app);
const wss = new WebSocketServer({ server });
setupWebSocket(wss);

// Start
async function start() {
  // Connect to MongoDB (non-blocking — app works without it)
  await connectDB();

  server.listen(PORT, () => {
    logger.success('SERVER', `🚀 HTTP server running on http://localhost:${PORT}`);
    logger.success('SERVER', `🔌 WebSocket server running on ws://localhost:${PORT}`);
    logger.info('SERVER', `📡 API docs at http://localhost:${PORT}/api`);
  });
}

start();
