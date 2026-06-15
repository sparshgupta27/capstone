import { Router } from 'express';
import Waypoint from '../models/Waypoint.js';

const router = Router();

// GET /api/waypoints — list all waypoints
router.get('/', async (req, res) => {
  try {
    const { status } = req.query;
    const filter = status ? { status } : {};
    const waypoints = await Waypoint.find(filter).sort({ createdAt: -1 }).lean();
    res.json({ count: waypoints.length, data: waypoints });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/waypoints — create a waypoint
router.post('/', async (req, res) => {
  try {
    const { x, y, label, missionId } = req.body;
    const waypoint = await Waypoint.create({ x, y, label, missionId });
    res.status(201).json({ data: waypoint });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// PATCH /api/waypoints/:id — update waypoint status
router.patch('/:id', async (req, res) => {
  try {
    const updates = req.body;
    if (updates.status === 'reached') {
      updates.reachedAt = new Date();
    }
    const waypoint = await Waypoint.findByIdAndUpdate(req.params.id, updates, { new: true });
    if (!waypoint) return res.status(404).json({ error: 'Waypoint not found' });
    res.json({ data: waypoint });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// DELETE /api/waypoints/:id — remove a waypoint
router.delete('/:id', async (req, res) => {
  try {
    const waypoint = await Waypoint.findByIdAndDelete(req.params.id);
    if (!waypoint) return res.status(404).json({ error: 'Waypoint not found' });
    res.json({ message: 'Waypoint deleted', data: waypoint });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

export default router;
