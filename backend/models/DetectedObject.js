import mongoose from 'mongoose';

const detectedObjectSchema = new mongoose.Schema({
  label: { type: String, required: true },         // "chair", "person", "fire_extinguisher", etc.
  confidence: { type: Number, required: true },     // 0.0 - 1.0
  bbox: {
    x: { type: Number, required: true },
    y: { type: Number, required: true },
    w: { type: Number, required: true },
    h: { type: Number, required: true },
  },
  worldPos: {
    x: { type: Number, required: true },
    y: { type: Number, required: true },
  },
  missionId: { type: mongoose.Schema.Types.ObjectId, ref: 'Mission' },
  timestamp: { type: Date, default: Date.now, index: true },
});

// Compound index for filtered queries
detectedObjectSchema.index({ label: 1, timestamp: -1 });

const DetectedObject = mongoose.model('DetectedObject', detectedObjectSchema);
export default DetectedObject;
