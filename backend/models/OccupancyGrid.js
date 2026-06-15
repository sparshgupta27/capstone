import mongoose from 'mongoose';

const occupancyGridSchema = new mongoose.Schema({
  width: { type: Number, required: true },          // number of cells in x
  height: { type: Number, required: true },         // number of cells in y
  resolution: { type: Number, required: true },     // meters per cell
  origin: {
    x: { type: Number, required: true },            // world x of grid origin
    y: { type: Number, required: true },            // world y of grid origin
  },
  data: { type: [Number], required: true },         // flattened 2D: 0=free, 1=occupied, -1=unknown
  missionId: { type: mongoose.Schema.Types.ObjectId, ref: 'Mission' },
  timestamp: { type: Date, default: Date.now },
});

// Keep only recent grid snapshots
occupancyGridSchema.index({ timestamp: 1 }, { expireAfterSeconds: 7200 }); // 2h TTL

const OccupancyGrid = mongoose.model('OccupancyGrid', occupancyGridSchema);
export default OccupancyGrid;
