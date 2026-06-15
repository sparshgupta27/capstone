/**
 * Canvas drawing helpers for the rover map.
 */

const COLORS = {
  gridFree: 'rgba(0, 212, 255, 0.06)',
  gridOccupied: 'rgba(0, 212, 255, 0.5)',
  gridUnknown: 'rgba(0, 0, 0, 0)',
  gridLines: 'rgba(0, 212, 255, 0.04)',
  walls: '#00d4ff',
  wallGlow: 'rgba(0, 212, 255, 0.3)',
  robot: '#00ff88',
  robotGlow: 'rgba(0, 255, 136, 0.4)',
  robotArrow: '#00ff88',
  pathTrail: 'rgba(0, 212, 255, 0.35)',
  pathTrailFade: 'rgba(0, 212, 255, 0.02)',
  waypoint: '#ffaa00',
  waypointGlow: 'rgba(255, 170, 0, 0.3)',
  detection: '#ff4466',
  detectionGlow: 'rgba(255, 68, 102, 0.3)',
  text: 'rgba(255, 255, 255, 0.5)',
};

/**
 * Draw the background grid pattern
 */
export function drawBackgroundGrid(ctx, transform, canvasWidth, canvasHeight) {
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  // Background
  ctx.fillStyle = '#060a14';
  ctx.fillRect(0, 0, canvasWidth, canvasHeight);

  // Grid lines every 1 meter
  ctx.strokeStyle = COLORS.gridLines;
  ctx.lineWidth = 0.5;
  for (let x = 0; x <= transform.worldWidth; x++) {
    const p = transform.toCanvas(x, 0);
    ctx.beginPath();
    ctx.moveTo(p.x, transform.offsetY);
    ctx.lineTo(p.x, transform.offsetY + transform.worldHeight * transform.scale);
    ctx.stroke();
  }
  for (let y = 0; y <= transform.worldHeight; y++) {
    const p = transform.toCanvas(0, y);
    ctx.beginPath();
    ctx.moveTo(transform.offsetX, p.y);
    ctx.lineTo(transform.offsetX + transform.worldWidth * transform.scale, p.y);
    ctx.stroke();
  }
}

/**
 * Draw the occupancy grid overlay
 */
export function drawOccupancyGrid(ctx, transform, gridData) {
  if (!gridData) return;

  const { width, height, resolution, data, origin } = gridData;
  const cellSize = resolution * transform.scale;

  for (let gy = 0; gy < height; gy++) {
    for (let gx = 0; gx < width; gx++) {
      const val = data[gy * width + gx];
      if (val === -1) continue; // skip unknown

      const wx = (origin?.x || 0) + (gx + 0.5) * resolution;
      const wy = (origin?.y || 0) + (gy + 0.5) * resolution;
      const p = transform.toCanvas(wx, wy);

      if (val === 1) {
        ctx.fillStyle = COLORS.gridOccupied;
      } else {
        ctx.fillStyle = COLORS.gridFree;
      }

      ctx.fillRect(p.x - cellSize / 2, p.y - cellSize / 2, cellSize, cellSize);
    }
  }
}

/**
 * Draw floor plan walls
 */
export function drawWalls(ctx, transform, walls) {
  ctx.strokeStyle = COLORS.walls;
  ctx.lineWidth = 2;
  ctx.shadowColor = COLORS.wallGlow;
  ctx.shadowBlur = 8;

  for (const wall of walls) {
    const p1 = transform.toCanvas(wall.x1, wall.y1);
    const p2 = transform.toCanvas(wall.x2, wall.y2);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
  }

  ctx.shadowBlur = 0;
}

/**
 * Draw the path trail with fading
 */
export function drawPathTrail(ctx, transform, pathHistory) {
  if (pathHistory.length < 2) return;

  const len = pathHistory.length;
  for (let i = 1; i < len; i++) {
    const alpha = (i / len) * 0.4;
    ctx.strokeStyle = `rgba(0, 212, 255, ${alpha})`;
    ctx.lineWidth = 1.5;
    const p1 = transform.toCanvas(pathHistory[i - 1].x, pathHistory[i - 1].y);
    const p2 = transform.toCanvas(pathHistory[i].x, pathHistory[i].y);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
  }
}

/**
 * Draw the robot as a circle with direction arrow
 */
export function drawRobot(ctx, transform, pose) {
  const p = transform.toCanvas(pose.x, pose.y);
  const size = Math.max(8, transform.scale * 0.3);

  // Glow
  ctx.shadowColor = COLORS.robotGlow;
  ctx.shadowBlur = 16;

  // Circle
  ctx.fillStyle = COLORS.robot;
  ctx.beginPath();
  ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
  ctx.fill();

  ctx.shadowBlur = 0;

  // Inner dot
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(p.x, p.y, size * 0.35, 0, Math.PI * 2);
  ctx.fill();

  // Direction arrow
  const arrowLen = size * 2.5;
  // In canvas, theta=0 means right, but we flipped Y
  const canvasTheta = -pose.theta; // flip for canvas coords
  const ax = p.x + Math.cos(canvasTheta) * arrowLen;
  const ay = p.y + Math.sin(canvasTheta) * arrowLen;

  ctx.strokeStyle = COLORS.robotArrow;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(p.x, p.y);
  ctx.lineTo(ax, ay);
  ctx.stroke();

  // Arrowhead
  const headLen = 6;
  const headAngle = 0.5;
  ctx.fillStyle = COLORS.robotArrow;
  ctx.beginPath();
  ctx.moveTo(ax, ay);
  ctx.lineTo(
    ax - headLen * Math.cos(canvasTheta - headAngle),
    ay - headLen * Math.sin(canvasTheta - headAngle)
  );
  ctx.lineTo(
    ax - headLen * Math.cos(canvasTheta + headAngle),
    ay - headLen * Math.sin(canvasTheta + headAngle)
  );
  ctx.closePath();
  ctx.fill();
}

/**
 * Draw waypoint markers
 */
export function drawWaypoints(ctx, transform, waypoints) {
  for (const wp of waypoints) {
    if (wp.status === 'cancelled') continue;

    const p = transform.toCanvas(wp.x, wp.y);

    // Glow ring
    ctx.strokeStyle = COLORS.waypointGlow;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 12, 0, Math.PI * 2);
    ctx.stroke();

    // Outer ring
    ctx.strokeStyle = COLORS.waypoint;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
    ctx.stroke();

    // Inner dot (filled if active/reached)
    if (wp.status === 'active' || wp.status === 'reached') {
      ctx.fillStyle = wp.status === 'reached' ? '#00ff88' : COLORS.waypoint;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Label
    if (wp.label) {
      ctx.font = '10px Inter, sans-serif';
      ctx.fillStyle = COLORS.text;
      ctx.textAlign = 'center';
      ctx.fillText(wp.label, p.x, p.y - 16);
    }
  }
}

/**
 * Draw detection markers on the map
 */
export function drawDetections(ctx, transform, detections) {
  for (const det of detections.slice(0, 20)) { // show last 20 on map
    if (!det.world_pos) continue;

    const p = transform.toCanvas(det.world_pos.x, det.world_pos.y);
    const alpha = det.isNew ? 1 : 0.5;

    // Diamond marker
    ctx.fillStyle = `rgba(255, 68, 102, ${alpha * 0.6})`;
    ctx.shadowColor = det.isNew ? COLORS.detectionGlow : 'transparent';
    ctx.shadowBlur = det.isNew ? 12 : 0;

    ctx.beginPath();
    ctx.moveTo(p.x, p.y - 6);
    ctx.lineTo(p.x + 5, p.y);
    ctx.lineTo(p.x, p.y + 6);
    ctx.lineTo(p.x - 5, p.y);
    ctx.closePath();
    ctx.fill();

    ctx.shadowBlur = 0;

    // Label
    ctx.font = '9px Inter, sans-serif';
    ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.7})`;
    ctx.textAlign = 'center';
    ctx.fillText(det.label, p.x, p.y - 10);
  }
}

/**
 * Draw scale indicator
 */
export function drawScale(ctx, transform, canvasHeight) {
  const scaleMeters = 2;
  const scalePixels = scaleMeters * transform.scale;
  const x = transform.offsetX + 10;
  const y = canvasHeight - 20;

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + scalePixels, y);
  ctx.moveTo(x, y - 4);
  ctx.lineTo(x, y + 4);
  ctx.moveTo(x + scalePixels, y - 4);
  ctx.lineTo(x + scalePixels, y + 4);
  ctx.stroke();

  ctx.font = '10px JetBrains Mono, monospace';
  ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.textAlign = 'center';
  ctx.fillText(`${scaleMeters}m`, x + scalePixels / 2, y - 8);
}
