/**
 * World-to-canvas coordinate transforms.
 * The floor plan is in meters; the canvas is in pixels.
 */

export function createTransform(canvasWidth, canvasHeight, worldWidth, worldHeight, padding = 40) {
  const scaleX = (canvasWidth - padding * 2) / worldWidth;
  const scaleY = (canvasHeight - padding * 2) / worldHeight;
  const scale = Math.min(scaleX, scaleY);
  const offsetX = (canvasWidth - worldWidth * scale) / 2;
  const offsetY = (canvasHeight - worldHeight * scale) / 2;

  return {
    scale,
    offsetX,
    offsetY,
    worldWidth,
    worldHeight,

    // World coords → canvas pixels
    toCanvas(wx, wy) {
      return {
        x: offsetX + wx * scale,
        y: offsetY + (worldHeight - wy) * scale, // flip Y: world Y goes up, canvas Y goes down
      };
    },

    // Canvas pixels → world coords
    toWorld(cx, cy) {
      return {
        x: (cx - offsetX) / scale,
        y: worldHeight - (cy - offsetY) / scale,
      };
    },
  };
}
