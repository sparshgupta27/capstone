import { useState, useEffect, useCallback, useRef } from 'react';

const MAX_DETECTIONS = 50;
const MAX_PATH_POINTS = 500;
const MAX_CHART_POINTS = 60;

/**
 * Central telemetry state management.
 * Processes WebSocket messages and maintains all dashboard state.
 */
export default function useTelemetry(lastMessage) {
  const [pose, setPose] = useState({ x: 0, y: 0, theta: 0, vx: 0, vtheta: 0 });
  const [battery, setBattery] = useState({ level: 100, charging: false });
  const [robotStatus, setRobotStatus] = useState({ state: 'idle', speed: 0 });
  const [grid, setGrid] = useState(null);
  const [detections, setDetections] = useState([]);
  const [waypoints, setWaypoints] = useState([]);
  const [pathHistory, setPathHistory] = useState([]);
  const [missionState, setMissionState] = useState({ active: false, name: '' });

  // Chart data (rolling window)
  const [speedHistory, setSpeedHistory] = useState([]);
  const [batteryHistory, setBatteryHistory] = useState([]);
  const [detectionRate, setDetectionRate] = useState([]);
  const detectionCountRef = useRef(0);

  // Process incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const { event, data } = lastMessage;

    switch (event) {
      case 'pose_update':
        setPose(data);
        setPathHistory(prev => {
          const next = [...prev, { x: data.x, y: data.y }];
          return next.length > MAX_PATH_POINTS ? next.slice(-MAX_PATH_POINTS) : next;
        });
        break;

      case 'battery':
        setBattery({ level: data.level, charging: data.charging });
        break;

      case 'status':
        setRobotStatus({ state: data.state, speed: data.speed });
        break;

      case 'grid_update':
        setGrid(data);
        break;

      case 'detection':
        detectionCountRef.current += 1;
        setDetections(prev => {
          const next = [{ ...data, id: Date.now() + Math.random(), isNew: true }, ...prev];
          // Clear "new" flag after 2 seconds
          setTimeout(() => {
            setDetections(curr =>
              curr.map(d => d.id === next[0].id ? { ...d, isNew: false } : d)
            );
          }, 2000);
          return next.slice(0, MAX_DETECTIONS);
        });
        break;

      case 'waypoint_added':
        setWaypoints(prev => [...prev, { ...data, status: data.status || 'pending' }]);
        break;

      case 'waypoint_cancelled':
        setWaypoints(prev =>
          prev.map(w => w.id === data.waypointId ? { ...w, status: 'cancelled' } : w)
        );
        break;

      case 'mission_started':
        setMissionState({ active: true, name: data.name || 'Active Mission' });
        break;

      case 'mission_ended':
        setMissionState({ active: false, name: '' });
        break;

      case 'mission_paused':
        setMissionState(prev => ({ ...prev, active: false }));
        break;
    }
  }, [lastMessage]);

  // Update chart histories every second
  useEffect(() => {
    const interval = setInterval(() => {
      setSpeedHistory(prev => {
        const next = [...prev, robotStatus.speed];
        return next.length > MAX_CHART_POINTS ? next.slice(-MAX_CHART_POINTS) : next;
      });
      setBatteryHistory(prev => {
        const next = [...prev, battery.level];
        return next.length > MAX_CHART_POINTS ? next.slice(-MAX_CHART_POINTS) : next;
      });
      setDetectionRate(prev => {
        const next = [...prev, detectionCountRef.current];
        detectionCountRef.current = 0;
        return next.length > MAX_CHART_POINTS ? next.slice(-MAX_CHART_POINTS) : next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [robotStatus.speed, battery.level]);

  const clearPath = useCallback(() => setPathHistory([]), []);
  const removeWaypoint = useCallback((id) => {
    setWaypoints(prev => prev.filter(w => w.id !== id));
  }, []);

  return {
    pose,
    battery,
    robotStatus,
    grid,
    detections,
    waypoints,
    pathHistory,
    missionState,
    speedHistory,
    batteryHistory,
    detectionRate,
    clearPath,
    removeWaypoint,
    setWaypoints,
  };
}
