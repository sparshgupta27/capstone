import logger from '../utils/logger.js';
import { isDBConnected } from '../config/db.js';

// Lazy imports — only use models when DB is connected
let RobotPose, DetectedObject, OccupancyGrid, Waypoint, Mission;
async function loadModels() {
  if (isDBConnected()) {
    RobotPose = (await import('../models/RobotPose.js')).default;
    DetectedObject = (await import('../models/DetectedObject.js')).default;
    OccupancyGrid = (await import('../models/OccupancyGrid.js')).default;
    Waypoint = (await import('../models/Waypoint.js')).default;
    Mission = (await import('../models/Mission.js')).default;
    logger.info('WS', 'Database models loaded');
  }
}

// Track connected clients by role
const clients = {
  dashboards: new Set(),
  publishers: new Set(),
};

// Latest state in memory — this is the primary source of truth for real-time data
const latestState = {
  pose: null,
  battery: null,
  status: null,
  grid: null,
};

// In-memory waypoint/mission tracking (works without DB)
let waypointCounter = 0;
const inMemoryWaypoints = [];
let currentMission = null;

/**
 * Broadcast a message to all dashboard clients
 */
function broadcastToDashboards(event, data) {
  const message = JSON.stringify({ event, data, timestamp: Date.now() });
  for (const ws of clients.dashboards) {
    if (ws.readyState === 1) {
      ws.send(message);
    }
  }
}

/**
 * Broadcast a message to all publisher clients
 */
function broadcastToPublishers(event, data) {
  const message = JSON.stringify({ event, data, timestamp: Date.now() });
  for (const ws of clients.publishers) {
    if (ws.readyState === 1) {
      ws.send(message);
    }
  }
}

/**
 * Handle incoming telemetry from the mock publisher
 */
function handleTelemetry(ws, payload) {
  const { type } = payload;

  switch (type) {
    case 'odom':
      latestState.pose = payload;
      broadcastToDashboards('pose_update', payload);
      // Async DB persist (fire and forget) — only if DB is up
      if (isDBConnected() && RobotPose && Math.random() < 0.2) {
        RobotPose.create({
          x: payload.x, y: payload.y, theta: payload.theta,
          vx: payload.vx, vtheta: payload.vtheta,
          timestamp: new Date(payload.timestamp),
        }).catch(() => {});
      }
      break;

    case 'lidar':
      broadcastToDashboards('lidar_update', payload);
      break;

    case 'detection':
      broadcastToDashboards('detection', payload);
      if (isDBConnected() && DetectedObject) {
        DetectedObject.create({
          label: payload.label, confidence: payload.confidence,
          bbox: payload.bbox, worldPos: payload.world_pos,
          timestamp: new Date(payload.timestamp),
        }).catch(() => {});
      }
      break;

    case 'battery':
      latestState.battery = payload;
      broadcastToDashboards('battery', payload);
      break;

    case 'status':
      latestState.status = payload;
      broadcastToDashboards('status', payload);
      break;

    case 'grid':
      latestState.grid = payload;
      broadcastToDashboards('grid_update', payload);
      break;

    default:
      logger.warn('WS', `Unknown telemetry type: ${type}`);
  }
}

/**
 * Handle commands from dashboard clients
 */
function handleDashboardCommand(ws, payload) {
  const { event, data } = payload;

  switch (event) {
    case 'set_waypoint': {
      waypointCounter++;
      const wpId = `wp_${waypointCounter}`;
      const waypoint = {
        id: wpId,
        x: data.x,
        y: data.y,
        label: data.label || `WP-${waypointCounter}`,
        status: 'pending',
      };
      inMemoryWaypoints.push(waypoint);
      logger.info('WS', `Waypoint set: (${data.x}, ${data.y}) "${waypoint.label}"`);

      broadcastToPublishers('new_waypoint', waypoint);
      broadcastToDashboards('waypoint_added', waypoint);
      break;
    }

    case 'cancel_waypoint': {
      const wp = inMemoryWaypoints.find(w => w.id === data.waypointId);
      if (wp) wp.status = 'cancelled';
      logger.info('WS', `Waypoint cancelled: ${data.waypointId}`);
      broadcastToPublishers('cancel_waypoint', data);
      broadcastToDashboards('waypoint_cancelled', data);
      break;
    }

    case 'mission_control': {
      logger.info('WS', `Mission control: ${data.action}`);
      if (data.action === 'start') {
        currentMission = {
          name: data.name || `Mission ${new Date().toLocaleTimeString()}`,
          startedAt: Date.now(),
        };
        broadcastToDashboards('mission_started', { name: currentMission.name });
        broadcastToPublishers('mission_start', {});
      } else if (data.action === 'stop') {
        broadcastToDashboards('mission_ended', { name: currentMission?.name });
        broadcastToPublishers('mission_stop', {});
        currentMission = null;
      } else if (data.action === 'pause') {
        broadcastToPublishers('mission_pause', {});
        broadcastToDashboards('mission_paused', {});
      }
      break;
    }

    default:
      logger.warn('WS', `Unknown dashboard event: ${event}`);
  }
}

/**
 * Setup WebSocket connection handlers
 */
export function setupWebSocket(wss) {
  // Try to load models (non-blocking)
  loadModels().catch(() => {});

  wss.on('connection', (ws, req) => {
    const url = new URL(req.url, 'http://localhost');
    const role = url.searchParams.get('role') || 'dashboard';

    if (role === 'publisher') {
      clients.publishers.add(ws);
      logger.success('WS', `Publisher connected (${clients.publishers.size} total)`);
    } else {
      clients.dashboards.add(ws);
      logger.success('WS', `Dashboard connected (${clients.dashboards.size} total)`);

      // Send latest state to newly connected dashboard immediately
      const sendState = (event, data) => {
        if (data) ws.send(JSON.stringify({ event, data, timestamp: Date.now() }));
      };
      sendState('pose_update', latestState.pose);
      sendState('battery', latestState.battery);
      sendState('status', latestState.status);
      sendState('grid_update', latestState.grid);

      // Send existing waypoints
      for (const wp of inMemoryWaypoints) {
        if (wp.status !== 'cancelled') {
          ws.send(JSON.stringify({ event: 'waypoint_added', data: wp, timestamp: Date.now() }));
        }
      }
      // Send mission state
      if (currentMission) {
        ws.send(JSON.stringify({ event: 'mission_started', data: { name: currentMission.name }, timestamp: Date.now() }));
      }
    }

    ws.on('message', (raw) => {
      try {
        const payload = JSON.parse(raw.toString());
        if (role === 'publisher') {
          handleTelemetry(ws, payload);
        } else {
          handleDashboardCommand(ws, payload);
        }
      } catch (error) {
        logger.error('WS', `Message error: ${error.message}`);
      }
    });

    ws.on('close', () => {
      if (role === 'publisher') {
        clients.publishers.delete(ws);
        logger.warn('WS', `Publisher disconnected (${clients.publishers.size} remaining)`);
      } else {
        clients.dashboards.delete(ws);
        logger.warn('WS', `Dashboard disconnected (${clients.dashboards.size} remaining)`);
      }
    });

    ws.on('error', (error) => {
      logger.error('WS', `Connection error: ${error.message}`);
    });
  });

  logger.info('WS', 'WebSocket handler initialized');
}

export function getLatestState() {
  return latestState;
}

export function getClientCounts() {
  return {
    dashboards: clients.dashboards.size,
    publishers: clients.publishers.size,
  };
}
