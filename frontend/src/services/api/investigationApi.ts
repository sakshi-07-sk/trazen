import {
  InvestigationCase,
  InvestigationStats,
  CopilotMessage,
} from "@/types/investigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export class ApiError extends Error {
  code: string;
  status: number;
  details?: unknown;

  constructor(message: string, status = 500, code = "UNKNOWN_ERROR", details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const investigationApi = {
  async getStats(): Promise<InvestigationStats> {
    const res = await fetch(`${API_BASE_URL}/api/stats`);
    if (!res.ok) {
      throw new ApiError("Failed to fetch investigation statistics", res.status);
    }
    return res.json();
  },

  async getInvestigations(): Promise<InvestigationCase[]> {
    const res = await fetch(`${API_BASE_URL}/api/investigations`);
    if (!res.ok) {
      throw new ApiError("Failed to fetch investigations list", res.status);
    }
    return res.json();
  },

  async getInvestigationById(id: string): Promise<InvestigationCase> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(id)}`);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new ApiError(
        errorData.message || `Failed to fetch investigation ${id}`,
        res.status,
        errorData.code || "FETCH_FAILED",
        errorData
      );
    }
    return res.json();
  },

  async createInvestigation(params: {
    target: string;
    network: "ETH" | "BTC";
    type: "address" | "transaction";
    maxHops: number;
    timeRange?: { from?: string; to?: string };
    mode?: "auto" | "demo" | "live";
  }): Promise<InvestigationCase> {
    const res = await fetch(`${API_BASE_URL}/api/investigations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new ApiError(
        data.message || "Investigation creation failed",
        res.status,
        data.code || "CREATION_FAILED",
        data
      );
    }

    return data;
  },

  async askCopilot(params: {
    caseId: string;
    query: string;
    history: CopilotMessage[];
  }): Promise<{ message: string; evidenceIds: string[]; findings: string[]; isOffline: boolean }> {
    const res = await fetch(`${API_BASE_URL}/api/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new ApiError(
        data.message || "TraceAI service encountered an issue",
        res.status,
        data.code || "COPILOT_FAILED",
        data
      );
    }

    return data;
  },

  async verifyAuditChain(caseId: string): Promise<{
    verified: boolean;
    recordsCount: number;
    headHash: string;
    chainIntegrity: "INTACT" | "TAMPERED";
    details: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/api/audit/verify?caseId=${encodeURIComponent(caseId)}`);
    if (!res.ok) {
      throw new ApiError("Failed to verify audit ledger hash chain", res.status);
    }
    return res.json();
  },
};
