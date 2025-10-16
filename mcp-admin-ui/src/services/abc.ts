import { api } from "./api";

interface CreateAnalysisRequestData {
  title: string;
}

interface GetAnalysisResponseData {
  id: number;
  title: string;
  status: string; // Could be 'active', 'inactive', etc.
  userId: number;
  created_at?: Date;
  updated_at?: Date;
}

interface GetAnalysisConversationResponseData {
    id: number;
    userId: number;
    messageBy: "ai" | "user"; // Indicates who sent the message
    ts: number; // Timestamp of the conversation in milliseconds
    text: string; // The text of the conversation
    stepName: string; // Name of the step in the conversation
    analysisId: number; // Foreign key to the analysis this conversation belongs to
    isConfirmationMessage: boolean; // Indicates if this is a confirmation message
    created_at?: Date;
    updated_at?: Date;
}

interface CreateAnalysisConversationRequestData {
  text: string; // The text of the conversation
}

interface GetAllStepsResponseData {
  id: string; // Unique identifier for the step
  name: string;
  description: string;
}

export const abcService = {
  async createAnalysis(createAnalysisRequestData: CreateAnalysisRequestData) {
    return api.post<GetAnalysisResponseData>("/api/v1/abc/analysis", createAnalysisRequestData);
  },

  async getAnalysis(analysisId: number) {
    return api.get<GetAnalysisResponseData>(`/api/v1/abc/analysis/${analysisId}`);
  },

  async getAllAnalyses() {
    return api.get<GetAnalysisResponseData[]>("/api/v1/abc/analysis");
  },

  async getLatestActiveAnalysis() {
    return api.get<GetAnalysisResponseData>("/api/v1/abc/analysis/latest-active");
  },

  async updateAnalysisTitle(analysisId: number, title: string) {
    return api.put<GetAnalysisResponseData>(`/api/v1/abc/analysis/${analysisId}`, { title });
  },

  async getAnalysisConversations(analysisId: number) {
    return api.get<GetAnalysisConversationResponseData[]>(`/api/v1/abc/analysis/${analysisId}/conversations`);
  },

  async createAnalysisConversation(analysisId: number, conversationData: CreateAnalysisConversationRequestData) {
    return api.post<GetAnalysisConversationResponseData>(`/api/v1/abc/analysis/${analysisId}/conversations`, conversationData);
  },

  async getAllSteps() {
    return api.get<GetAllStepsResponseData[]>("/api/v1/abc/all-steps");
  },

  async getAnalysisConversationStepSummary(analysisId: number, stepName: string) {
    return api.get<{ summary?: string }>(`/api/v1/abc/analysis/${analysisId}/conversations/steps/${stepName}/summary`);
  }
};