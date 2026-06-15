import { Router } from 'express';
import Mission from '../models/Mission.js';

const router = Router();

// GET /api/missions — list all missions
router.get('/', async (req, res) => {
  try {
    const { status } = req.query;
    const filter = status ? { status } : {};
    const missions = await Mission.find(filter).sort({ startedAt: -1 }).lean();
    res.json({ count: missions.length, data: missions });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/missions — create a mission
router.post('/', async (req, res) => {
  try {
    const { name } = req.body;
    const mission = await Mission.create({
      name: name || `Mission ${new Date().toLocaleString()}`,
      status: 'planning',
    });
    res.status(201).json({ data: mission });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// GET /api/missions/:id — get mission details
router.get('/:id', async (req, res) => {
  try {
    const mission = await Mission.findById(req.params.id).populate('waypointIds').lean();
    if (!mission) return res.status(404).json({ error: 'Mission not found' });
    res.json({ data: mission });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// PATCH /api/missions/:id — update mission
router.patch('/:id', async (req, res) => {
  try {
    const updates = req.body;
    if (updates.status === 'active') updates.startedAt = new Date();
    if (updates.status === 'completed' || updates.status === 'aborted') updates.endedAt = new Date();

    const mission = await Mission.findByIdAndUpdate(req.params.id, updates, { new: true });
    if (!mission) return res.status(404).json({ error: 'Mission not found' });
    res.json({ data: mission });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// GET /api/missions/:id/stats — mission statistics
router.get('/:id/stats', async (req, res) => {
  try {
    const mission = await Mission.findById(req.params.id).lean();
    if (!mission) return res.status(404).json({ error: 'Mission not found' });

    const duration = mission.endedAt
      ? (new Date(mission.endedAt) - new Date(mission.startedAt)) / 1000
      : mission.startedAt
        ? (Date.now() - new Date(mission.startedAt)) / 1000
        : 0;

    res.json({
      data: {
        ...mission.stats,
        duration,
        status: mission.status,
      },
    });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
