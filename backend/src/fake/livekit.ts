/**
 * Fake LiveKit token generation
 * In production, this would call the real LiveKit API
 */

/**
 * Generates a fake LiveKit access token
 * This is a placeholder function that simulates LiveKit token generation
 * 
 * @param roomId - The ID of the LiveKit room
 * @param identity - The user's identity/username
 * @returns A fake token string
 */
export function generateFakeLiveKitToken(roomId: string, identity: string): string {
  const timestamp = Date.now();
  const token = `FAKE_LIVEKIT_TOKEN_${roomId}_${identity}_${timestamp}`;
  
  console.log(`[LIVEKIT] Generated fake token for room: ${roomId}, identity: ${identity}`);
  
  return token;
}

/**
 * Additional fake function to simulate token validation
 * @param token - The token to validate
 * @returns Always returns true in this fake implementation
 */
export function validateFakeLiveKitToken(token: string): boolean {
  console.log(`[LIVEKIT] Validating fake token: ${token.substring(0, 30)}...`);
  return token.startsWith('FAKE_LIVEKIT_TOKEN_');
}
