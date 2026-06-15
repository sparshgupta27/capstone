import { useRef, useEffect, useCallback, useState } from 'react';
import { createTransform } from '../utils/transforms';
import {
  drawBackgroundGrid,
  drawOccupancyGrid,
  drawWalls,
  drawPathTrail,
  drawRobot,
  drawWaypoints,
  drawDetections,
  drawScale,
} from '../utils/gridRenderer';

// Floor plan walls (same as config.json)
const WALLS = [
  { x1: 0, y1: 0, x2: 20, y2: 0 },
  { x1: 20, y1: 0, x2: 20, y2: 20 },
  { x1: 20, y1: 20, x2: 0, y2: 20 },
  { x1: 0, y1: 20, x2: 0, y2: 0 },
  { x1: 0, y1: 7, x2: 5, y2: 7 },
  { x1: 7, y1: 7, x2: 12, y2: 7 },
  { x1: 5, y1: 0, x2: 5, y2: 5 },
  { x1: 12, y1: 0, x2: 12, y2: 5 },
  { x1: 12, y1: 7, x2: 12, y2: 14 },
  { x1: 0, y1: 14, x2: 8, y2: 14 },
  { x1: 10, y1: 14, x2: 20, y2: 14 },
  { x1: 15, y1: 7, x2: 15, y2: 14 },
  { x1: 15, y1: 7, x2: 20, y2: 7 },
];

const WORLD_W = 20;
const WORLD_H = 20;

export default function MapCanvas({ pose, grid, pathHistory, waypoints, detections, onMapClick }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const transformRef = useRef(null);
  const [mouseCoord, setMouseCoord] = useState(null);
  const sizeRef = useRef({ width: 100, height: 100 });

  // Handle resize with ResizeObserver
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateSize = () => {
      const rect = container.getBoundingClientRect();
      const w = Math.floor(rect.width) || 100;
      const h = Math.floor(rect.height) || 100;
      sizeRef.current = { width: w, height: h };
      transformRef.current = createTransform(w, h, WORLD_W, WORLD_H);
    };

    const observer = new ResizeObserver(updateSize);
    observer.observe(container);
    updateSize();

    return () => observer.disconnect();
  }, []);

  // Render using requestAnimationFrame for smooth updates
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const { width, height } = sizeRef.current;
    const transform = transformRef.current;
    if (!transform || width <= 0 || height <= 0) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // Draw all layers
    drawBackgroundGrid(ctx, transform, width, height);
    drawOccupancyGrid(ctx, transform, grid);
    drawWalls(ctx, transform, WALLS);
    drawPathTrail(ctx, transform, pathHistory);
    drawDetections(ctx, transform, detections);
    drawWaypoints(ctx, transform, waypoints);
    drawRobot(ctx, transform, pose);
    drawScale(ctx, transform, height);
  });

  // Handle click to set waypoint
  const handleClick = useCallback((e) => {
    const transform = transformRef.current;
    if (!transform) return;
    const rect = e.target.getBoundingClientRect();
    const world = transform.toWorld(e.clientX - rect.left, e.clientY - rect.top);
    if (world.x >= 0 && world.x <= WORLD_W && world.y >= 0 && world.y <= WORLD_H) {
      onMapClick?.(world.x, world.y);
    }
  }, [onMapClick]);

  // Mouse move for coordinate display
  const handleMouseMove = useCallback((e) => {
    const transform = transformRef.current;
    if (!transform) return;
    const rect = e.target.getBoundingClientRect();
    const world = transform.toWorld(e.clientX - rect.left, e.clientY - rect.top);
    if (world.x >= 0 && world.x <= WORLD_W && world.y >= 0 && world.y <= WORLD_H) {
      setMouseCoord(world);
    } else {
      setMouseCoord(null);
    }
  }, []);

  return (
    <div className="map-container" ref={containerRef}>
      <canvas
        ref={canvasRef}
        className="map-canvas"
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setMouseCoord(null)}
      />
      <div className="map-overlay">
        <button className="map-control-btn" title="Reset view">⟳</button>
      </div>
      <div className="map-legend">
        <div className="legend-item">
          <div className="legend-swatch" style={{ background: '#00ff88' }} />
          <span>Robot</span>
        </div>
        <div className="legend-item">
          <div className="legend-swatch" style={{ background: '#00d4ff' }} />
          <span>Walls</span>
        </div>
        <div className="legend-item">
          <div className="legend-swatch" style={{ background: '#ffaa00', borderRadius: '50%' }} />
          <span>Waypoint</span>
        </div>
        <div className="legend-item">
          <div className="legend-swatch" style={{ background: '#ff4466', transform: 'rotate(45deg)' }} />
          <span>Detection</span>
        </div>
      </div>
      {mouseCoord && (
        <div className="coord-display">
          {mouseCoord.x.toFixed(1)}, {mouseCoord.y.toFixed(1)} m
        </div>
      )}
    </div>
  );
}
