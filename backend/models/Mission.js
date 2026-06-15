import mongoose from 'mongoose';

const missionSchema = new mongoose.Schema({
  name: { type: String, required: true },
  status: {
    type: String,
    enum: ['planning', 'active', 'completed', 'aborted'],
    default: 'planning',
  },
  startedAt: { type: Date },
  endedAt: { type: Date },
  waypointIds: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Waypoint' }],
  stats: {
    distanceTraveled: { type: Number, default: 0 },
    objectsDetected: { type: Number, default: 0 },
    duration: { type: Number, default: 0 },            // seconds
    areaCovered: { type: Number, default: 0 },          // square meters
  },
});

const Mission = mongoose.model('Mission', missionSchema);
export default Mission;
