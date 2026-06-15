const OBJECT_ICONS = {
  chair: '🪑',
  desk: '🪵',
  door: '🚪',
  fire_extinguisher: '🧯',
  person: '🧑',
  box: '📦',
  trash_bin: '🗑️',
  monitor: '🖥️',
  bookshelf: '📚',
  plant: '🌿',
};

const OBJECT_COLORS = {
  chair: 'rgba(0, 212, 255, 0.15)',
  desk: 'rgba(139, 90, 43, 0.15)',
  door: 'rgba(255, 170, 0, 0.15)',
  fire_extinguisher: 'rgba(255, 68, 102, 0.15)',
  person: 'rgba(0, 255, 136, 0.15)',
  box: 'rgba(255, 200, 100, 0.15)',
  trash_bin: 'rgba(128, 128, 128, 0.15)',
  monitor: 'rgba(100, 149, 237, 0.15)',
  bookshelf: 'rgba(160, 82, 45, 0.15)',
  plant: 'rgba(34, 139, 34, 0.15)',
};

function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export default function DetectionFeed({ detections }) {
  return (
    <div className="panel">
      <div className="panel__header">
        <span className="panel__title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="6" />
            <circle cx="12" cy="12" r="2" />
          </svg>
          Detections
        </span>
        <span className="panel__badge">{detections.length}</span>
      </div>
      <div className="panel__content">
        {detections.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span>No detections yet</span>
          </div>
        ) : (
          <div className="detection-feed">
            {detections.map((det) => (
              <div
                key={det.id}
                className={`detection-item ${det.isNew ? 'new' : ''}`}
              >
                <div
                  className="detection-item__icon"
                  style={{ background: OBJECT_COLORS[det.label] || 'rgba(255,255,255,0.1)' }}
                >
                  {OBJECT_ICONS[det.label] || '❓'}
                </div>
                <div className="detection-item__info">
                  <div className="detection-item__label">{det.label?.replace(/_/g, ' ')}</div>
                  <div className="detection-item__meta">
                    ({det.world_pos?.x?.toFixed(1)}, {det.world_pos?.y?.toFixed(1)}) · {formatTime(det.timestamp)}
                  </div>
                </div>
                <span className="detection-item__confidence">
                  {(det.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
