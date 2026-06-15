import { useCallback } from 'react';
import useWebSocket from './hooks/useWebSocket';
import useTelemetry from './hooks/useTelemetry';
import StatusBar from './components/StatusBar';
import MapCanvas from './components/MapCanvas';
import TelemetryPanel from './components/TelemetryPanel';
import DetectionFeed from './components/DetectionFeed';
import WaypointPanel from './components/WaypointPanel';
import MissionControl from './components/MissionControl';
import MiniChart from './components/MiniChart';

const WS_URL = 'ws://localhost:5000?role=dashboard';

export default function App() {
  const { isConnected, lastMessage, sendMessage } = useWebSocket(WS_URL);
  const telemetry = useTelemetry(lastMessage);

  // Handle map click → set waypoint
  const handleMapClick = useCallback((x, y) => {
    const label = `WP-${(telemetry.waypoints.length + 1).toString().padStart(2, '0')}`;
    sendMessage('set_waypoint', { x: parseFloat(x.toFixed(2)), y: parseFloat(y.toFixed(2)), label });
  }, [sendMessage, telemetry.waypoints.length]);

  // Handle waypoint cancel
  const handleCancelWaypoint = useCallback((waypointId) => {
    sendMessage('cancel_waypoint', { waypointId });
    telemetry.removeWaypoint(waypointId);
  }, [sendMessage, telemetry.removeWaypoint]);

  // Handle mission actions
  const handleMissionAction = useCallback((action) => {
    const name = action === 'start' ? `Mission ${new Date().toLocaleTimeString()}` : undefined;
    sendMessage('mission_control', { action, name });
  }, [sendMessage]);

  return (
    <div className="app">
      {/* Top Status Bar */}
      <StatusBar isConnected={isConnected} missionState={telemetry.missionState} />

      {/* Left Sidebar */}
      <div className="sidebar">
        <TelemetryPanel
          pose={telemetry.pose}
          battery={telemetry.battery}
          robotStatus={telemetry.robotStatus}
        />
        <MissionControl
          missionState={telemetry.missionState}
          onMissionAction={handleMissionAction}
        />
        <WaypointPanel
          waypoints={telemetry.waypoints}
          onCancelWaypoint={handleCancelWaypoint}
        />
        <DetectionFeed detections={telemetry.detections} />
      </div>

      {/* Main Content */}
      <div className="main-content">
        <MapCanvas
          pose={telemetry.pose}
          grid={telemetry.grid}
          pathHistory={telemetry.pathHistory}
          waypoints={telemetry.waypoints}
          detections={telemetry.detections}
          onMapClick={handleMapClick}
        />

        {/* Bottom Charts */}
        <div className="charts-panel">
          <MiniChart
            data={telemetry.speedHistory}
            color="#00d4ff"
            label="Speed"
            currentValue={telemetry.robotStatus.speed.toFixed(2)}
            unit=" m/s"
          />
          <MiniChart
            data={telemetry.batteryHistory}
            color="#00ff88"
            label="Battery"
            currentValue={telemetry.battery.level.toFixed(0)}
            unit="%"
          />
          <MiniChart
            data={telemetry.detectionRate}
            color="#ff4466"
            label="Detections"
            currentValue={telemetry.detections.length}
            unit=" total"
          />
        </div>
      </div>
    </div>
  );
}
