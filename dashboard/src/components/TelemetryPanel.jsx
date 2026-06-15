export default function TelemetryPanel({ pose, battery, robotStatus }) {
  const batteryClass = battery.level > 50 ? 'high' : battery.level > 20 ? 'medium' : 'low';

  return (
    <div className="panel">
      <div className="panel__header">
        <span className="panel__title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          Telemetry
        </span>
        <span className={`state-badge ${robotStatus.state}`}>
          {robotStatus.state}
        </span>
      </div>
      <div className="panel__content">
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="telemetry-item__label">Position X</span>
            <span className="telemetry-item__value">
              {pose.x.toFixed(2)}<span className="telemetry-item__unit">m</span>
            </span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-item__label">Position Y</span>
            <span className="telemetry-item__value">
              {pose.y.toFixed(2)}<span className="telemetry-item__unit">m</span>
            </span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-item__label">Heading</span>
            <span className="telemetry-item__value">
              {(pose.theta * 180 / Math.PI).toFixed(0)}<span className="telemetry-item__unit">°</span>
            </span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-item__label">Speed</span>
            <span className="telemetry-item__value">
              {robotStatus.speed.toFixed(2)}<span className="telemetry-item__unit">m/s</span>
            </span>
          </div>
          <div className="telemetry-item" style={{ gridColumn: '1 / -1' }}>
            <span className="telemetry-item__label">Battery</span>
            <span className="telemetry-item__value">
              {battery.level.toFixed(0)}<span className="telemetry-item__unit">%</span>
              {battery.charging && ' ⚡'}
            </span>
            <div className="battery-bar">
              <div
                className={`battery-bar__fill ${batteryClass}`}
                style={{ width: `${battery.level}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
