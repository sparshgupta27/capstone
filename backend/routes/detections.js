import { Router } from 'express';
import DetectedObject from '../models/DetectedObject.js';

const router = Router();

// GET /api/detections — filtered detection history
router.get('/', async (req, res) => {
  try {
    const { from, to, label, limit = 50 } = req.query;

    const filter = {};
    if (from || to) {
      filter.timestamp = {};
      if (from) filter.timestamp.$gte = new Date(from);
      if (to) filter.timestamp.$lte = new Date(to);
    }
    if (label) {
      filter.label = label;
    }

    const detections = await DetectedObject.find(filter)
      .sort({ timestamp: -1 })
      .limit(parseInt(limit))
      .lean();

    res.json({ count: detections.length, data: detections });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET /api/detections/stats — detection count by label
router.get('/stats', async (req, res) => {
  try {
    const stats = await DetectedObject.aggregate([
      { $group: { _id: '$label', count: { $sum: 1 }, avgConfidence: { $avg: '$confidence' } } },
      { $sort: { count: -1 } },
    ]);

    res.json({ data: stats });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
