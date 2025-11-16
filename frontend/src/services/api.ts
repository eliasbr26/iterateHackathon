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
  interview_id: number;
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
  // ==================== EXISTING LIVEKIT APIs ====================
  async createRoom(
    roomName?: string,
    maxParticipants: number = 10,
    candidateId?: number
  ): Promise<CreateRoomResponse> {
    const response = await fetch(`${API_BASE_URL}/rooms/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room_name: roomName,
        max_participants: maxParticipants,
        candidate_id: candidateId,
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

  // ==================== PILLAR 1: CO-PILOT ====================
  async getCoPilotSuggestions(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/copilot/suggestions`);

    if (!response.ok) {
      throw new Error(`Failed to get co-pilot suggestions: ${response.statusText}`);
    }

    return response.json();
  },

  async getCoverageStatus(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/copilot/coverage`);

    if (!response.ok) {
      throw new Error(`Failed to get coverage status: ${response.statusText}`);
    }

    return response.json();
  },

  // ==================== PILLAR 3: QUESTION BANK ====================
  async getQuestionSuggestions(interviewId: number, context: any) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/questions/suggestions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(context),
    });

    if (!response.ok) {
      throw new Error(`Failed to get question suggestions: ${response.statusText}`);
    }

    return response.json();
  },

  async getAllQuestions(jobTitle?: string, competency?: string) {
    const params = new URLSearchParams();
    if (jobTitle) params.append('job_title', jobTitle);
    if (competency) params.append('competency', competency);

    const response = await fetch(`${API_BASE_URL}/questions?${params}`);

    if (!response.ok) {
      throw new Error(`Failed to get questions: ${response.statusText}`);
    }

    return response.json();
  },

  // ==================== PILLAR 4: INTERVIEWER FEEDBACK ====================
  async analyzeQuestion(interviewId: number, question: string) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/analyze-question`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Failed to analyze question: ${response.statusText}`);
    }

    return response.json();
  },

  async getCurrentFeedback(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/feedback/current`);

    if (!response.ok) {
      throw new Error(`Failed to get current feedback: ${response.statusText}`);
    }

    return response.json();
  },

  // ==================== PILLAR 5: INTERVIEWS & REPORTS ====================
  async listInterviews(page: number = 1, limit: number = 20) {
    const response = await fetch(`${API_BASE_URL}/interviews?page=${page}&limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to list interviews: ${response.statusText}`);
    }

    return response.json();
  },

  async getInterview(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}`);

    if (!response.ok) {
      throw new Error(`Failed to get interview: ${response.statusText}`);
    }

    return response.json();
  },

  async generateSummary(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/generate-summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to generate summary: ${response.statusText}`);
    }

    return response.json();
  },

  async generateReport(interviewId: number, reportType: string, format: string = 'json') {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/generate-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ report_type: reportType, format }),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate report: ${response.statusText}`);
    }

    if (format === 'html' || format === 'markdown') {
      return response.text();
    }

    return response.json();
  },

  async getReports(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/reports`);

    if (!response.ok) {
      throw new Error(`Failed to get reports: ${response.statusText}`);
    }

    return response.json();
  },

  // ==================== PILLAR 7: RAG ASSISTANT ====================
  async askAssistant(interviewId: number, question: string, context: any) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        interview_context: context,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to ask assistant: ${response.statusText}`);
    }

    return response.json();
  },

  async getAssistantHistory(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/assistant-history`);

    if (!response.ok) {
      throw new Error(`Failed to get assistant history: ${response.statusText}`);
    }

    return response.json();
  },

  async clearAssistantHistory(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/assistant-history`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to clear assistant history: ${response.statusText}`);
    }

    return response.json();
  },

  async getKnowledgeStats() {
    const response = await fetch(`${API_BASE_URL}/knowledge/stats`);

    if (!response.ok) {
      throw new Error(`Failed to get knowledge stats: ${response.statusText}`);
    }

    return response.json();
  },

  async uploadDocument(
    file: File,
    options: {
      doc_type?: string;
      title?: string;
      description?: string;
    } = {}
  ) {
    const formData = new FormData();
    formData.append('file', file);

    if (options.doc_type) formData.append('doc_type', options.doc_type);
    if (options.title) formData.append('title', options.title);
    if (options.description) formData.append('description', options.description);

    const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Failed to upload document');
    }

    return response.json();
  },

  // ==================== PILLAR 6: CANDIDATE PROFILES ====================
  async uploadCandidateCV(
    file: File,
    options: {
      candidate_name?: string;
      candidate_email?: string;
    } = {}
  ) {
    const formData = new FormData();
    formData.append('file', file);

    if (options.candidate_name) formData.append('candidate_name', options.candidate_name);
    if (options.candidate_email) formData.append('candidate_email', options.candidate_email);

    const response = await fetch(`${API_BASE_URL}/candidates/upload-cv`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Failed to upload CV');
    }

    return response.json();
  },

  async listCandidates() {
    const response = await fetch(`${API_BASE_URL}/candidates`);

    if (!response.ok) {
      throw new Error(`Failed to list candidates: ${response.statusText}`);
    }

    return response.json();
  },

  async getCandidateProfile(candidateId: number) {
    const response = await fetch(`${API_BASE_URL}/candidates/${candidateId}`);

    if (!response.ok) {
      throw new Error(`Failed to get candidate profile: ${response.statusText}`);
    }

    return response.json();
  },

  async updateCandidateProfile(candidateId: number, updateData: any) {
    const response = await fetch(`${API_BASE_URL}/candidates/${candidateId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update candidate: ${response.statusText}`);
    }

    return response.json();
  },

  async linkInterviewToCandidate(interviewId: number, candidateId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/link-candidate/${candidateId}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to link interview: ${response.statusText}`);
    }

    return response.json();
  },

  async processInterviewCompletion(interviewId: number) {
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/process-completion`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to process interview: ${response.statusText}`);
    }

    return response.json();
  },
};
