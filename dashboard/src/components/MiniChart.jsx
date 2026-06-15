import { useRef, useEffect } from 'react';

/**
 * Sparkline chart component — renders a simple line chart on canvas.
 */
export default function MiniChart({ data, color = '#00d4ff', label, currentValue, unit }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const container = canvas.parentElement;
    const rect = container.getBoundingClientRect();
    const width = Math.floor(rect.width);
    const height = Math.floor(rect.height);

    if (width <= 0 || height <= 0) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // Clear
    ctx.clearRect(0, 0, width, height);

    if (data.length < 2) return;

    const max = Math.max(...data, 1);
    const min = Math.min(...data, 0);
    const range = max - min || 1;
    const padding = 2;

    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    // Convert hex color to rgba for gradient
    const hexToRgba = (hex, alpha) => {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };
    gradient.addColorStop(0, hexToRgba(color, 0.2));
    gradient.addColorStop(1, 'transparent');

    ctx.beginPath();
    ctx.moveTo(padding, height);

    for (let i = 0; i < data.length; i++) {
      const x = padding + (i / (data.length - 1)) * (width - padding * 2);
      const y = height - padding - ((data[i] - min) / range) * (height - padding * 2);
      ctx.lineTo(x, y);
    }

    ctx.lineTo(width - padding, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    for (let i = 0; i < data.length; i++) {
      const x = padding + (i / (data.length - 1)) * (width - padding * 2);
      const y = height - padding - ((data[i] - min) / range) * (height - padding * 2);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Current value dot
    if (data.length > 0) {
      const lastX = width - padding;
      const lastY = height - padding - ((data[data.length - 1] - min) / range) * (height - padding * 2);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
      ctx.fill();

      // Glow
      ctx.shadowColor = color;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(lastX, lastY, 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }, [data, color]);

  return (
    <div className="chart-card">
      <div className="chart-card__header">
        <span className="chart-card__title">{label}</span>
        <span className="chart-card__value" style={{ color }}>
          {currentValue}{unit}
        </span>
      </div>
      <div className="sparkline-container">
        <canvas ref={canvasRef} className="sparkline-canvas" />
      </div>
    </div>
  );
}
