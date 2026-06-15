import { useState, useEffect } from 'react';

export default function StatusBar({ isConnected, missionState }) {
  const [clock, setClock] = useState(formatClock());

  useEffect(() => {
    const interval = setInterval(() => setClock(formatClock()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="status-bar" id="status-bar">
      <div className="status-bar__left">
        <div className="status-bar__logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
            <path d="M2 12h20" />
          </svg>
          ROVER COMMAND
        </div>
        <div className="status-bar__divider" />
        <span className="status-bar__mission">
          {missionState.active ? missionState.name : 'No Active Mission'}
        </span>
      </div>
      <div className="status-bar__right">
        <div className="connection-indicator">
          <div className={`connection-dot ${isConnected ? 'connected' : 'disconnected'}`} />
          <span style={{ color: isConnected ? 'var(--emerald)' : 'var(--red)' }}>
            {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>
        <div className="status-bar__divider" />
        <span className="status-bar__clock">{clock}</span>
      </div>
    </div>
  );
}

function formatClock() {
  return new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}
