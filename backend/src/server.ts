/**
 * Main server file for the Interview Analysis Backend
 * Handles HTTP requests and Socket.IO real-time communication
 */

import express, { Request, Response } from 'express';
import { createServer } from 'http';
import { Server, Socket } from 'socket.io';
import cors from 'cors';
import { generateFakeLiveKitToken } from './fake/livekit';
import { evaluateQuestionDifficulty } from './fake/llm';
import {
  addQuestion,
  calculateAverageDifficulty,
  getQuestionCount,
  initializeInterview,
  QuestionEval
} from './state';

// ============================================================================
// Server Configuration
// ============================================================================

const PORT = process.env.PORT || 3001;
const app = express();
const httpServer = createServer(app);

// Configure Socket.IO with CORS
const io = new Server(httpServer, {
  cors: {
    origin: '*', // In production, specify your frontend URL
    methods: ['GET', 'POST']
  }
});

// ============================================================================
// Middleware
// ============================================================================

app.use(cors());
app.use(express.json());

// Request logging middleware
app.use((req, _res, next) => {
  console.log(`[HTTP] ${req.method} ${req.path}`);
  next();
});

// ============================================================================
// HTTP Endpoints
// ============================================================================

/**
 * Health check endpoint
 */
app.get('/', (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    message: 'Interview Analysis Backend is running',
    timestamp: new Date().toISOString()
  });
});

/**
 * Generate a LiveKit token for a room and identity
 * Query params:
 *   - roomId: The interview room ID
 *   - identity: The user's identity/name
 */
app.get('/livekit-token', (req: Request, res: Response): void => {
  const { roomId, identity } = req.query;
  
  // Validate required parameters
  if (!roomId || !identity) {
    res.status(400).json({
      error: 'Missing required parameters',
      required: ['roomId', 'identity']
    });
    return;
  }
  
  try {
    // Generate fake token
    const token = generateFakeLiveKitToken(
      roomId as string,
      identity as string
    );
    
    console.log(`[ENDPOINT] Generated LiveKit token for room: ${roomId}, identity: ${identity}`);
    
    res.json({
      token,
      roomId,
      identity,
      timestamp: Date.now()
    });
  } catch (error) {
    console.error('[ENDPOINT] Error generating token:', error);
    res.status(500).json({
      error: 'Failed to generate token'
    });
  }
});

/**
 * Get statistics for a specific interview session
 */
app.get('/interview/:roomId/stats', (req: Request, res: Response) => {
  const { roomId } = req.params;
  
  try {
    const questionCount = getQuestionCount(roomId);
    const avgDifficulty = calculateAverageDifficulty(roomId);
    
    res.json({
      roomId,
      questionCount,
      avgDifficulty,
      timestamp: Date.now()
    });
  } catch (error) {
    console.error('[ENDPOINT] Error getting stats:', error);
    res.status(500).json({
      error: 'Failed to get interview stats'
    });
  }
});

// ============================================================================
// Socket.IO Event Handlers
// ============================================================================

/**
 * Interface for incoming question data from frontend
 */
interface QuestionNewPayload {
  roomId: string;
  text: string;
}

/**
 * Interface for difficulty update broadcast to frontend
 */
interface DifficultyUpdatePayload {
  roomId: string;
  question: QuestionEval;
  difficulty: number;
  avgDifficulty: number;
  questionIndex: number;
}

io.on('connection', (socket: Socket) => {
  console.log(`[SOCKET] Client connected: ${socket.id}`);
  
  /**
   * Handle client joining a specific room
   */
  socket.on('join:room', (roomId: string) => {
    socket.join(roomId);
    initializeInterview(roomId);
    console.log(`[SOCKET] Client ${socket.id} joined room: ${roomId}`);
    
    // Send current stats to the newly joined client
    const questionCount = getQuestionCount(roomId);
    const avgDifficulty = calculateAverageDifficulty(roomId);
    
    socket.emit('room:joined', {
      roomId,
      questionCount,
      avgDifficulty
    });
  });
  
  /**
   * Handle client leaving a specific room
   */
  socket.on('leave:room', (roomId: string) => {
    socket.leave(roomId);
    console.log(`[SOCKET] Client ${socket.id} left room: ${roomId}`);
  });
  
  /**
   * Handle new question received from frontend
   * This is the main event that triggers the analysis pipeline:
   * 1. Receive question text
   * 2. Evaluate difficulty using fake LLM
   * 3. Store in memory
   * 4. Calculate new average
   * 5. Broadcast update to all clients in the room
   */
  socket.on('question:new', async (payload: QuestionNewPayload) => {
    try {
      const { roomId, text } = payload;
      
      console.log(`[SOCKET] New question received in room ${roomId}: "${text.substring(0, 50)}..."`);
      
      // Initialize interview session if it doesn't exist
      initializeInterview(roomId);
      
      // Evaluate difficulty using fake LLM
      const difficulty = await evaluateQuestionDifficulty(text);
      
      // Create question evaluation object
      const questionEval: QuestionEval = {
        text,
        difficulty,
        timestamp: Date.now()
      };
      
      // Store in memory
      addQuestion(roomId, questionEval);
      
      // Calculate new average difficulty
      const avgDifficulty = calculateAverageDifficulty(roomId);
      const questionIndex = getQuestionCount(roomId);
      
      // Prepare update payload
      const updatePayload: DifficultyUpdatePayload = {
        roomId,
        question: questionEval,
        difficulty,
        avgDifficulty,
        questionIndex
      };
      
      console.log(`[SOCKET] Broadcasting difficulty update for room ${roomId}`);
      console.log(`[SOCKET] Question ${questionIndex}: Difficulty=${difficulty}/5, Average=${avgDifficulty}/5`);
      
      // Broadcast to all clients in the room
      io.to(roomId).emit('difficulty:update', updatePayload);
      
      // Also send acknowledgment to the sender
      socket.emit('question:processed', {
        success: true,
        questionIndex,
        difficulty,
        avgDifficulty
      });
      
    } catch (error) {
      console.error('[SOCKET] Error processing question:', error);
      
      // Send error to the sender
      socket.emit('question:error', {
        error: 'Failed to process question',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });
  
  /**
   * Handle manual reset of interview session
   */
  socket.on('interview:reset', (roomId: string) => {
    console.log(`[SOCKET] Resetting interview session: ${roomId}`);
    initializeInterview(roomId);
    
    // Broadcast reset to all clients in the room
    io.to(roomId).emit('interview:resetted', {
      roomId,
      timestamp: Date.now()
    });
  });
  
  /**
   * Handle client disconnect
   */
  socket.on('disconnect', () => {
    console.log(`[SOCKET] Client disconnected: ${socket.id}`);
  });
  
  /**
   * Handle ping for connection health check
   */
  socket.on('ping', () => {
    socket.emit('pong', { timestamp: Date.now() });
  });
});

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Global error handler for Express
 */
app.use((err: Error, _req: Request, res: Response, _next: any) => {
  console.error('[ERROR]', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// ============================================================================
// Server Startup
// ============================================================================

httpServer.listen(PORT, () => {
  console.log('========================================');
  console.log('🚀 Interview Analysis Backend Started');
  console.log('========================================');
  console.log(`📡 HTTP Server: http://localhost:${PORT}`);
  console.log(`🔌 WebSocket Server: ws://localhost:${PORT}`);
  console.log(`⏰ Started at: ${new Date().toISOString()}`);
  console.log('========================================');
  console.log('Available endpoints:');
  console.log(`  GET  /`);
  console.log(`  GET  /livekit-token?roomId=<id>&identity=<name>`);
  console.log(`  GET  /interview/:roomId/stats`);
  console.log('========================================');
  console.log('Socket.IO events:');
  console.log(`  📥 join:room`);
  console.log(`  📥 leave:room`);
  console.log(`  📥 question:new`);
  console.log(`  📥 interview:reset`);
  console.log(`  📤 difficulty:update`);
  console.log(`  📤 question:processed`);
  console.log('========================================');
});

// ============================================================================
// Graceful Shutdown
// ============================================================================

process.on('SIGTERM', () => {
  console.log('[SERVER] SIGTERM signal received: closing HTTP server');
  httpServer.close(() => {
    console.log('[SERVER] HTTP server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('[SERVER] SIGINT signal received: closing HTTP server');
  httpServer.close(() => {
    console.log('[SERVER] HTTP server closed');
    process.exit(0);
  });
});
