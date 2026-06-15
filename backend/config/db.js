import mongoose from 'mongoose';

let isConnected = false;

const connectDB = async () => {
  try {
    const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/rover';
    const conn = await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 3000,  // fail fast if no MongoDB
      bufferCommands: false,            // don't buffer when disconnected
    });
    isConnected = true;
    console.log(`✅ MongoDB connected: ${conn.connection.host}/${conn.connection.name}`);
    return conn;
  } catch (error) {
    isConnected = false;
    console.error(`❌ MongoDB not available: ${error.message}`);
    console.warn('⚠️  Running in DEMO MODE — no data persistence.');
    // Disable Mongoose buffering globally so DB calls fail immediately
    mongoose.set('bufferCommands', false);
    return null;
  }
};

export const isDBConnected = () => isConnected;

export default connectDB;
