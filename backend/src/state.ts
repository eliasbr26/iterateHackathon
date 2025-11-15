/**
 * In-memory data store for interview sessions
 * Stores all questions and their difficulty evaluations
 */

/**
 * Represents a single evaluated question
 */
export interface QuestionEval {
  text: string;
  difficulty: number;
  timestamp: number;
}

/**
 * Represents an interview session with all its questions
 */
export interface InterviewData {
  questions: QuestionEval[];
}

/**
 * Global in-memory store
 * Key: roomId (interview session ID)
 * Value: InterviewData containing all questions for that session
 */
export const interviews: Record<string, InterviewData> = {};

/**
 * Initialize a new interview session
 * @param roomId - The unique identifier for the interview room
 */
export function initializeInterview(roomId: string): void {
  if (!interviews[roomId]) {
    interviews[roomId] = {
      questions: []
    };
    console.log(`[STATE] Initialized new interview session: ${roomId}`);
  }
}

/**
 * Add a question evaluation to an interview session
 * @param roomId - The interview room ID
 * @param question - The question evaluation to add
 */
export function addQuestion(roomId: string, question: QuestionEval): void {
  initializeInterview(roomId);
  interviews[roomId].questions.push(question);
  console.log(`[STATE] Added question to ${roomId}. Total questions: ${interviews[roomId].questions.length}`);
}

/**
 * Get all questions for an interview session
 * @param roomId - The interview room ID
 * @returns Array of question evaluations
 */
export function getQuestions(roomId: string): QuestionEval[] {
  initializeInterview(roomId);
  return interviews[roomId].questions;
}

/**
 * Calculate the average difficulty of all questions in a session
 * @param roomId - The interview room ID
 * @returns Average difficulty score (0 if no questions)
 */
export function calculateAverageDifficulty(roomId: string): number {
  const questions = getQuestions(roomId);
  
  if (questions.length === 0) {
    return 0;
  }
  
  const sum = questions.reduce((acc, q) => acc + q.difficulty, 0);
  const average = sum / questions.length;
  
  return Math.round(average * 100) / 100; // Round to 2 decimal places
}

/**
 * Get the number of questions in a session
 * @param roomId - The interview room ID
 * @returns Number of questions
 */
export function getQuestionCount(roomId: string): number {
  return getQuestions(roomId).length;
}

/**
 * Clear all data for an interview session
 * @param roomId - The interview room ID
 */
export function clearInterview(roomId: string): void {
  delete interviews[roomId];
  console.log(`[STATE] Cleared interview session: ${roomId}`);
}

/**
 * Get all active room IDs
 * @returns Array of room IDs
 */
export function getAllRoomIds(): string[] {
  return Object.keys(interviews);
}
