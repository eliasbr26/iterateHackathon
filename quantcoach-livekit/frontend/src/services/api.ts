const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface CreateRoomResponse {
  sid: string;
  name: string;
  max_participants: number;
  creation_time: number;
  interviewer_token: string;
  candidate_token: string;
  agent_token: string;
  url: string;
}

export interface GenerateTokenRequest {
  room_name: string;
  participant_identity: string;
  participant_name?: string;
  role: 'interviewer' | 'candidate' | 'agent' | 'participant';
}

export interface GenerateTokenResponse {
  token: string;
  room_name: string;
  participant_identity: string;
  url: string;
}

export interface Analytics {
  room: string;
  total_evaluations: number;
  total_transcripts: number;
  difficulty_distribution: {
    easy: number;
    medium: number;
    hard: number;
    unknown: number;
  };
  topic_coverage: {
    [topic: string]: boolean;
  };
  average_tone: 'harsh' | 'neutral' | 'encouraging';
  red_flag_count: number;
  average_confidence: {
    subject: number;
    difficulty: number;
    tone: number;
  };
  evaluations_sample?: any[];
}

export interface AgentStatus {
  room: string;
  status: 'running' | 'stopped' | 'error' | 'completed';
  started_at: string;
  error?: string;
}

export const api = {
  async createRoom(roomName?: string, maxParticipants: number = 10): Promise<CreateRoomResponse> {
    const response = await fetch(`${API_BASE_URL}/rooms/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room_name: roomName,
        max_participants: maxParticipants,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create room: ${response.statusText}`);
    }

    return response.json();
  },

  async generateToken(request: GenerateTokenRequest): Promise<GenerateTokenResponse> {
    const response = await fetch(`${API_BASE_URL}/tokens/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate token: ${response.statusText}`);
    }

    return response.json();
  },

  async listRooms() {
    const response = await fetch(`${API_BASE_URL}/rooms`);

    if (!response.ok) {
      throw new Error(`Failed to list rooms: ${response.statusText}`);
    }

    return response.json();
  },

  async getRoomParticipants(roomName: string) {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomName}/participants`);

    if (!response.ok) {
      throw new Error(`Failed to get participants: ${response.statusText}`);
    }

    return response.json();
  },

  async deleteRoom(roomName: string) {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomName}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete room: ${response.statusText}`);
    }

    return response.json();
  },

  async getAnalytics(roomName: string): Promise<Analytics> {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomName}/analytics`);

    if (!response.ok) {
      throw new Error(`Failed to get analytics: ${response.statusText}`);
    }

    return response.json();
  },

  async getAgentStatus(roomName: string): Promise<AgentStatus> {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomName}/status`);

    if (!response.ok) {
      throw new Error(`Failed to get agent status: ${response.statusText}`);
    }

    return response.json();
  },
};
