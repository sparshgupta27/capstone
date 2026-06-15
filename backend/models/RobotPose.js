import mongoose from 'mongoose';

const robotPoseSchema = new mongoose.Schema({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  theta: { type: Number, required: true },       // orientation in radians
  vx: { type: Number, default: 0 },              // linear velocity m/s
  vtheta: { type: Number, default: 0 },           // angular velocity rad/s
  missionId: { type: mongoose.Schema.Types.ObjectId, ref: 'Mission' },
  timestamp: { type: Date, default: Date.now },
}, {
  timestamps: false,
  // TTL index — auto-delete poses older than 1 hour to prevent unbounded growth
  expireAfterSeconds: 3600,
});

// TTL index on timestamp
robotPoseSchema.index({ timestamp: 1 }, { expireAfterSeconds: 3600 });

const RobotPose = mongoose.model('RobotPose', robotPoseSchema);
export default RobotPose;
