/**
 * Camera Module - Handles webcam feed, frame capture, and vision processing
 * Supports real-time video display and frame analysis
 */

const fs = require('fs');
const path = require('path');

class CameraModule {
  constructor() {
    this.cameraActive = false;
    this.frames = [];
    this.maxFrames = 50; // Keep last 50 frames (User Request)
  }

  /**
   * Initialize camera (frontend-side via WebRTC)
   * Backend provides endpoints for frame storage and processing
   */
  initializeCamera() {
    this.cameraActive = true;
    console.log('📷 Camera initialized');
    return { status: 'ready', message: 'Camera ready for stream' };
  }

  /**
   * Handle incoming frame data from frontend (base64 encoded)
   */
  processFrame(frameData, metadata = {}) {
    try {
      if (this.frames.length >= this.maxFrames) {
        this.frames.shift(); // Remove oldest frame
      }

      this.frames.push({
        timestamp: Date.now(),
        data: frameData,
        metadata: metadata
      });

      return { success: true, frameCount: this.frames.length };
    } catch (e) {
      console.error('Frame processing error:', e);
      return { success: false, error: e.message };
    }
  }

  /**
   * Save current frame to disk (for vision processing)
   */
  captureFrame(filename = `frame_${Date.now()}.jpg`) {
    try {
      if (this.frames.length === 0) {
        return { success: false, error: 'No frames available' };
      }

      const latestFrame = this.frames[this.frames.length - 1];
      const storagePath = path.join(__dirname, 'storage', 'frames', filename);

      // Ensure directory exists
      if (!fs.existsSync(path.dirname(storagePath))) {
        fs.mkdirSync(path.dirname(storagePath), { recursive: true });
      }

      // Extract base64 and save
      const base64Data = latestFrame.data.replace(/^data:image\/\w+;base64,/, '');
      fs.writeFileSync(storagePath, base64Data, 'base64');

      // Optimization: Cleanup old frames from disk (Keep max 50)
      this.cleanupStorage();

      return {
        success: true,
        filepath: storagePath,
        timestamp: latestFrame.timestamp
      };
    } catch (e) {
      console.error('Frame capture error:', e);
      return { success: false, error: e.message };
    }
  }

  /**
   * Get current camera status
   */
  getStatus() {
    return {
      active: this.cameraActive,
      frameCount: this.frames.length,
      latestFrame: this.frames.length > 0 ? this.frames[this.frames.length - 1].timestamp : null
    };
  }

  /**
   * Stop camera
   */
  stopCamera() {
    this.cameraActive = false;
    this.frames = [];
    console.log('📷 Camera stopped');
    return { status: 'stopped' };
  }

  /**
   * Get frame for vision processing (returns latest frame or specific index)
   */
  getFrame(index = -1) {
    const frameIndex = index === -1 ? this.frames.length - 1 : index;
    if (frameIndex < 0 || frameIndex >= this.frames.length) {
      return null;
    }
    return this.frames[frameIndex];
  }

  /**
   * Get all frames (for analysis)
   */
  getAllFrames() {
    return this.frames;
  }

  /**
   * Cleanup old stored frames to save space
   * Keeps only the 50 most recent files in storage/frames
   */
  cleanupStorage() {
    try {
      const framesDir = path.join(__dirname, 'storage', 'frames');
      if (!fs.existsSync(framesDir)) return;

      const files = fs.readdirSync(framesDir);
      if (files.length <= 50) return;

      // Sort by time (assuming filename contains timestamp frame_TIMESTAMP.jpg)
      // or just by creation time if needed. Filenames are typically reliable here.
      files.sort(); // String sort works for frame_TIMESTAMP if standardized, otherwise use stat.

      // Files to delete (Oldest first)
      const deleteCount = files.length - 50;
      for (let i = 0; i < deleteCount; i++) {
        fs.unlinkSync(path.join(framesDir, files[i]));
      }
      console.log(`🧹 Cleaned up ${deleteCount} old frames to save storage.`);
    } catch (err) {
      console.error("Cleanup error:", err);
    }
  }
}

module.exports = CameraModule;
