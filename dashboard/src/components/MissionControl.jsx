export default function MissionControl({ missionState, onMissionAction }) {
  return (
    <div className="panel">
      <div className="panel__header">
        <span className="panel__title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 00-2.91-.09z" />
            <path d="M12 15l-3-3a22 22 0 012-3.95A12.88 12.88 0 0122 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 01-4 2z" />
          </svg>
          Mission Control
        </span>
        {missionState.active && (
          <span className="panel__badge" style={{ background: 'rgba(0,255,136,0.15)', color: '#00ff88' }}>
            LIVE
          </span>
        )}
      </div>
      <div className="panel__content">
        {missionState.active && missionState.name && (
          <div style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            marginBottom: 'var(--gap-sm)',
            fontFamily: 'var(--font-mono)',
          }}>
            {missionState.name}
          </div>
        )}
        <div className="mission-controls">
          {!missionState.active ? (
            <button
              className="btn btn--start"
              onClick={() => onMissionAction?.('start')}
            >
              ▶ Start
            </button>
          ) : (
            <>
              <button
                className="btn btn--pause"
                onClick={() => onMissionAction?.('pause')}
              >
                ⏸ Pause
              </button>
              <button
                className="btn btn--stop"
                onClick={() => onMissionAction?.('stop')}
              >
                ■ Stop
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
