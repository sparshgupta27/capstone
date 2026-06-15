import { Router } from 'express';
import RobotPose from '../models/RobotPose.js';

const router = Router();

// GET /api/telemetry — historical pose data
router.get('/', async (req, res) => {
  try {
    const { from, to, limit = 100 } = req.query;

    const filter = {};
    if (from || to) {
      filter.timestamp = {};
      if (from) filter.timestamp.$gte = new Date(from);
      if (to) filter.timestamp.$lte = new Date(to);
    }

    const poses = await RobotPose.find(filter)
      .sort({ timestamp: -1 })
      .limit(parseInt(limit))
      .lean();

    res.json({ count: poses.length, data: poses });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET /api/telemetry/latest — most recent pose
router.get('/latest', async (req, res) => {
  try {
    const pose = await RobotPose.findOne().sort({ timestamp: -1 }).lean();
    res.json({ data: pose });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
