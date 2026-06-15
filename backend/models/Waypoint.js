import mongoose from 'mongoose';

const waypointSchema = new mongoose.Schema({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  label: { type: String, default: '' },
  status: {
    type: String,
    enum: ['pending', 'active', 'reached', 'cancelled'],
    default: 'pending',
  },
  missionId: { type: mongoose.Schema.Types.ObjectId, ref: 'Mission' },
  createdAt: { type: Date, default: Date.now },
  reachedAt: { type: Date },
});

const Waypoint = mongoose.model('Waypoint', waypointSchema);
export default Waypoint;
