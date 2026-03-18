import { APP_CONFIG } from "@/lib/config";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? APP_CONFIG.backendUrl;

export class BackendApiError extends Error {
  status: number;
  errorCode?: string;

  constructor(message: string, status: number, errorCode?: string) {
    super(message);
    this.name = "BackendApiError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

type ErrorDetailObject = {
  message?: string;
  errorCode?: string;
};

type ErrorBody = {
  detail?: string | ErrorDetailObject;
  message?: string;
  errorCode?: string;
};

async function toApiError(response: Response, errorLabel: string): Promise<BackendApiError> {
  let fallbackMessage = `${errorLabel} failed (${response.status})`;
  try {
    const body = (await response.json()) as ErrorBody;
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim()) {
      fallbackMessage = `${errorLabel} failed (${response.status}): ${detail}`;
      return new BackendApiError(fallbackMessage, response.status, body.errorCode);
    }
    if (detail && typeof detail === "object") {
      const message = typeof detail.message === "string" && detail.message.trim() ? detail.message : fallbackMessage;
      const errorCode =
        typeof detail.errorCode === "string" && detail.errorCode.trim()
          ? detail.errorCode
          : typeof body.errorCode === "string"
            ? body.errorCode
            : undefined;
      const fullMessage = `${errorLabel} failed (${response.status}): ${message}`;
      return new BackendApiError(fullMessage, response.status, errorCode);
    }
    if (typeof body.message === "string" && body.message.trim()) {
      fallbackMessage = `${errorLabel} failed (${response.status}): ${body.message}`;
      return new BackendApiError(fallbackMessage, response.status, body.errorCode);
    }
  } catch {
    // Keep fallback text when response body is not JSON.
  }
  return new BackendApiError(fallbackMessage, response.status);
}

async function apiPost<T>(path: string, body?: unknown, errorLabel = "Request"): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw await toApiError(response, errorLabel);
  }
  return (await response.json()) as T;
}

async function apiGet<T>(path: string, errorLabel = "Request"): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    method: "GET",
    credentials: "include",
  });
  if (!response.ok) {
    throw await toApiError(response, errorLabel);
  }
  return (await response.json()) as T;
}

export type WorkspaceResponse = {
  userId: string;
  thread: { id: string; title: string };
  threads: Array<{ id: string; title: string; createdAt: string; updatedAt: string }>;
  documents: Array<{ key: string; title: string; content: string; currentRevisionId: string | null }>;
  messages: Array<{ id: number; role: "user" | "assistant" | "system"; content: string; createdAt: string }>;
  rules: Array<{ id: number; ruleText: string; createdAt: string }>;
};

export type SkillCatalogResponse = {
  skills: Array<{
    id: string;
    name: string;
    brief: string;
    enabled: boolean;
    allowedTools: string[];
  }>;
};

export type SkillDetail = {
  id: string;
  name: string;
  brief: string;
  prompt: string;
  enabled: boolean;
  allowedTools: string[];
  requiredOrder: string[];
  blockedCombinations: string[][];
};

export type RuleItem = {
  id: number;
  ruleText: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
};

export type MemoryPanelResponse = {
  userId: string;
  memories: Array<{
    id: number;
    key: string;
    value: string;
    type: string;
    confidence: number;
    updatedAt: string;
  }>;
  summary: string;
  summaryVersion: number;
};

export type MemoryDetail = {
  id: number;
  key: string;
  value: string;
  type: string;
  confidence: number;
  rationale: string;
  updatedAt: string;
};

export type WorkspaceSnapshot = {
  id: string;
  userId: string;
  parentSnapshotId: string | null;
  message: string;
  authorType: string;
  createdAt: string;
};

export const copilotClient = {
  getWorkspace(threadId: string | null): Promise<WorkspaceResponse> {
    return apiPost<WorkspaceResponse>("/copilot/workspace", { threadId }, "Workspace fetch");
  },
  async streamChatTurn(
    threadId: string,
    message: string,
    handlers: {
      onStart?: (payload: { threadId: string }) => void;
      onToken?: (payload: { text: string }) => void;
      onCompleted?: (payload: {
        threadId: string;
        assistantMessage: { id: number; role: string; content: string; createdAt: string };
        documents: Array<{ key: string; title: string; content: string; currentRevisionId: string | null }>;
      }) => void;
      onToolCalled?: (payload: { toolName: string; metadata: unknown }) => void;
      onSkillRequested?: (payload: { metadata: unknown }) => void;
      onSkillLoaded?: (payload: { metadata: unknown }) => void;
      onSkillRejected?: (payload: { metadata: unknown }) => void;
      onMemoryRetrieved?: (payload: { count: number }) => void;
      onFailed?: (payload: { error: string }) => void;
    },
  ): Promise<void> {
    const response = await fetch(`${BACKEND_URL}/copilot/chat/turn/stream`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ threadId, message }),
    });
    if (!response.ok) {
      throw await toApiError(response, "Chat stream");
    }
    if (!response.body) {
      throw new BackendApiError("Chat stream failed: empty body", 500);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const emitEvent = (eventName: string, payloadRaw: string): void => {
      let payload: unknown = {};
      try {
        payload = JSON.parse(payloadRaw);
      } catch {
        payload = { error: "invalid event payload" };
      }
      if (eventName === "turn_started") handlers.onStart?.(payload as { threadId: string });
      if (eventName === "token") handlers.onToken?.(payload as { text: string });
      if (eventName === "turn_completed")
        handlers.onCompleted?.(
          payload as {
            threadId: string;
            assistantMessage: { id: number; role: string; content: string; createdAt: string };
            documents: Array<{ key: string; title: string; content: string; currentRevisionId: string | null }>;
          },
        );
      if (eventName === "tool_called") handlers.onToolCalled?.(payload as { toolName: string; metadata: unknown });
      if (eventName === "skill_requested") handlers.onSkillRequested?.(payload as { metadata: unknown });
      if (eventName === "skill_loaded") handlers.onSkillLoaded?.(payload as { metadata: unknown });
      if (eventName === "skill_rejected") handlers.onSkillRejected?.(payload as { metadata: unknown });
      if (eventName === "memory_retrieved") handlers.onMemoryRetrieved?.(payload as { count: number });
      if (eventName === "turn_failed") handlers.onFailed?.(payload as { error: string });
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";
      for (const chunk of chunks) {
        const lines = chunk.split("\n");
        let eventName = "";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) data = line.slice(5).trim();
        }
        if (eventName) emitEvent(eventName, data);
      }
    }
  },
  createThread(title?: string): Promise<{ thread: { id: string; title: string; createdAt: string; updatedAt: string } }> {
    return apiPost("/copilot/threads/create", { title: title ?? null }, "Thread create");
  },
  deleteThread(threadId: string): Promise<{ deleted: boolean }> {
    return fetch(`${BACKEND_URL}/copilot/threads/${encodeURIComponent(threadId)}`, {
      method: "DELETE",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Thread delete");
      return (await response.json()) as { deleted: boolean };
    });
  },
  createDocument(
    title: string,
    docKey?: string,
    initialContent?: string,
  ): Promise<{ document: { key: string; title: string; content: string; currentRevisionId: string | null } }> {
    return apiPost(
      "/copilot/documents/create",
      { title, docKey: docKey ?? null, initialContent: initialContent ?? null },
      "Document create",
    );
  },
  addRule(ruleText: string): Promise<{ rule: { id: number; ruleText: string; isActive: boolean; createdAt: string } }> {
    return apiPost("/copilot/rules", { ruleText }, "Rule create");
  },
  updateWorkingDocument(
    docKey: string,
    content: string,
  ): Promise<{ document: { key: string; title: string; content: string; currentRevisionId: string | null } }> {
    return apiPost(`/copilot/documents/${encodeURIComponent(docKey)}/working`, { content }, "Working document update");
  },
  checkpointDocuments(message?: string): Promise<{
    revisions: Record<string, { id: string; docKey: string; message: string; createdAt: string }>;
  }> {
    return apiPost("/copilot/documents/checkpoint", { message: message ?? null }, "Document checkpoint");
  },
  createWorkspaceSnapshot(message?: string): Promise<{ snapshot: WorkspaceSnapshot }> {
    return apiPost("/copilot/workspace/snapshots", { message: message ?? null }, "Workspace snapshot create");
  },
  listWorkspaceSnapshots(limit = 50): Promise<{ snapshots: WorkspaceSnapshot[] }> {
    return apiPost("/copilot/workspace/snapshots/list", { limit }, "Workspace snapshots list");
  },
  restoreWorkspaceSnapshot(snapshotId: string, message?: string): Promise<{ snapshot: WorkspaceSnapshot }> {
    return apiPost(
      `/copilot/workspace/snapshots/${encodeURIComponent(snapshotId)}/restore`,
      { message: message ?? null },
      "Workspace snapshot restore",
    );
  },
  listDocumentRevisions(
    docKey: string,
    limit = 20,
  ): Promise<{
    revisions: Array<{ id: string; docKey: string; message: string; authorType: string; createdAt: string }>;
  }> {
    return apiPost(`/copilot/documents/${encodeURIComponent(docKey)}/revisions`, { limit }, "Document revisions list");
  },
  revertDocument(
    docKey: string,
    revisionId: string,
    message?: string,
  ): Promise<{ revision: { id: string; docKey: string; message: string; createdAt: string } }> {
    return apiPost(
      `/copilot/documents/${encodeURIComponent(docKey)}/revert`,
      { revisionId, message: message ?? null },
      "Document revert",
    );
  },
  deleteDocument(docKey: string): Promise<{ deleted: boolean }> {
    return fetch(`${BACKEND_URL}/copilot/documents/${encodeURIComponent(docKey)}`, {
      method: "DELETE",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Document delete");
      return (await response.json()) as { deleted: boolean };
    });
  },
  listSkills(): Promise<SkillCatalogResponse> {
    return apiGet<SkillCatalogResponse>("/copilot/skills", "Skills list");
  },
  getSkill(skillId: string): Promise<{ skill: SkillDetail }> {
    return apiGet<{ skill: SkillDetail }>(`/copilot/skills/${encodeURIComponent(skillId)}`, "Skill fetch");
  },
  updateSkill(
    skillId: string,
    payload: Omit<SkillDetail, "id">,
  ): Promise<{ skill: SkillDetail }> {
    return fetch(`${BACKEND_URL}/copilot/skills/${encodeURIComponent(skillId)}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Skill update");
      return (await response.json()) as { skill: SkillDetail };
    });
  },
  deleteSkill(skillId: string): Promise<{ deleted: boolean }> {
    return fetch(`${BACKEND_URL}/copilot/skills/${encodeURIComponent(skillId)}`, {
      method: "DELETE",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Skill delete");
      return (await response.json()) as { deleted: boolean };
    });
  },
  listRules(): Promise<{ rules: RuleItem[] }> {
    return apiGet<{ rules: RuleItem[] }>("/copilot/rules", "Rules list");
  },
  getRule(ruleId: number): Promise<{ rule: RuleItem }> {
    return apiGet<{ rule: RuleItem }>(`/copilot/rules/${ruleId}`, "Rule fetch");
  },
  updateRule(ruleId: number, payload: { ruleText: string; isActive: boolean }): Promise<{ rule: RuleItem }> {
    return fetch(`${BACKEND_URL}/copilot/rules/${ruleId}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Rule update");
      return (await response.json()) as { rule: RuleItem };
    });
  },
  deleteRule(ruleId: number): Promise<{ deleted: boolean }> {
    return fetch(`${BACKEND_URL}/copilot/rules/${ruleId}`, {
      method: "DELETE",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Rule delete");
      return (await response.json()) as { deleted: boolean };
    });
  },
  listMemories(): Promise<MemoryPanelResponse> {
    return apiGet<MemoryPanelResponse>("/copilot/memories", "Memories list");
  },
  getMemory(memoryId: number): Promise<{ memory: MemoryDetail }> {
    return apiGet<{ memory: MemoryDetail }>(`/copilot/memories/${memoryId}`, "Memory fetch");
  },
  updateMemory(
    memoryId: number,
    payload: {
      key: string;
      value: string;
      type: string;
      confidence: number;
      rationale: string;
    },
  ): Promise<{ memory: MemoryDetail }> {
    return fetch(`${BACKEND_URL}/copilot/memories/${memoryId}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Memory update");
      return (await response.json()) as { memory: MemoryDetail };
    });
  },
  deleteMemory(memoryId: number): Promise<{ deleted: boolean }> {
    return fetch(`${BACKEND_URL}/copilot/memories/${memoryId}`, {
      method: "DELETE",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Memory delete");
      return (await response.json()) as { deleted: boolean };
    });
  },
  updateMemorySummary(summary: string): Promise<{ summary: string; summaryVersion: number; updatedAt: string }> {
    return fetch(`${BACKEND_URL}/copilot/memories/summary`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ summary }),
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Memory summary update");
      return (await response.json()) as { summary: string; summaryVersion: number; updatedAt: string };
    });
  },
  deleteMemorySummary(): Promise<{ deleted: boolean }> {
    return fetch(`${BACKEND_URL}/copilot/memories/summary`, {
      method: "DELETE",
      credentials: "include",
    }).then(async (response) => {
      if (!response.ok) throw await toApiError(response, "Memory summary delete");
      return (await response.json()) as { deleted: boolean };
    });
  },
};

