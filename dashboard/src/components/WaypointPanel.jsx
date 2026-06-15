export default function WaypointPanel({ waypoints, onCancelWaypoint }) {
  const activeWaypoints = waypoints.filter(w => w.status !== 'cancelled');

  return (
    <div className="panel">
      <div className="panel__header">
        <span className="panel__title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          Waypoints
        </span>
        <span className="panel__badge">{activeWaypoints.length}</span>
      </div>
      <div className="panel__content">
        {activeWaypoints.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 4v16m8-8H4" />
            </svg>
            <span>Click on the map to add waypoints</span>
          </div>
        ) : (
          <div className="waypoint-list">
            {activeWaypoints.map((wp, i) => (
              <div key={wp.id || i} className="waypoint-item">
                <div className={`waypoint-item__marker ${wp.status}`} />
                <span className="waypoint-item__coords">
                  {wp.label ? `${wp.label} · ` : ''}
                  ({wp.x?.toFixed(1)}, {wp.y?.toFixed(1)})
                </span>
                <button
                  className="waypoint-item__delete"
                  onClick={() => onCancelWaypoint?.(wp.id)}
                  title="Cancel waypoint"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
