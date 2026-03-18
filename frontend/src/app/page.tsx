"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  ChatPane,
  ChatsRail,
  DocPane,
  DocsRail,
  type ChatMessage,
  type ExplorerItem,
  type ExplorerTab,
} from "@/features/workspace/components";
import {
  parseMemoryMarkdown,
  parseMemorySummaryMarkdown,
  parseRuleMarkdown,
  parseSkillMarkdown,
  toMemoryMarkdown,
  toMemorySummaryMarkdown,
  toRuleMarkdown,
  toSkillMarkdown,
} from "@/features/workspace/components/entity_markdown";
import {
  copilotClient,
  BackendApiError,
  type RuleItem,
  type SkillDetail,
  type WorkspaceResponse,
  type WorkspaceSnapshot,
} from "@/shared/api/copilot_client";
import { streamClient } from "@/shared/api/stream_client";

const STORAGE_CHAT_WIDTH = "cfai.workspace.chatWidth.v2";
const STORAGE_DOC_WIDTH = "cfai.workspace.docWidth.v2";
const STORAGE_CHAT_PANE_WIDTH = "cfai.workspace.chatPaneWidth.v2";
const STORAGE_DOCS_RAIL_WIDTH = "cfai.workspace.docsRailWidth.v1";
const STORAGE_PANE_VISIBILITY = "cfai.workspace.paneVisibility.v1";
const DOCS_RAIL_WIDTH = 180;
const SPLITTER_WIDTH = 6;
const CHATS_RAIL_WIDTH = 220;
const CHAT_PANE_WIDTH = 420;
const DOC_PANE_WIDTH = 420;

type PaneKey = "chats" | "chat" | "document" | "documents";
type PaneVisibility = Record<PaneKey, boolean>;
type PaneWidths = Record<PaneKey, number>;
type DragState = {
  leftPane: PaneKey;
  rightPane: PaneKey;
  startX: number;
  startLeftWidth: number;
  startRightWidth: number;
} | null;

type EditorEntityType = "document" | "skill" | "rule" | "memory" | "memory_summary";
type EditorEntity = {
  entityType: EditorEntityType;
  id: string;
  title: string;
};

const PANE_MIN: Record<PaneKey, number> = {
  chats: 160,
  chat: 240,
  document: 260,
  documents: 150,
};

export default function Home() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [activeExplorerTab, setActiveExplorerTab] = useState<ExplorerTab>("documents");
  const [activeExplorerItemId, setActiveExplorerItemId] = useState("");
  const [editorEntity, setEditorEntity] = useState<EditorEntity | null>(null);
  const [editorDraft, setEditorDraft] = useState("");
  const [paneVisibility, setPaneVisibility] = useState<PaneVisibility>({
    chats: true,
    chat: true,
    document: true,
    documents: true,
  });
  const [paneWidths, setPaneWidths] = useState<PaneWidths>({
    chats: CHATS_RAIL_WIDTH,
    chat: CHAT_PANE_WIDTH,
    document: DOC_PANE_WIDTH,
    documents: DOCS_RAIL_WIDTH,
  });
  const [dragState, setDragState] = useState<DragState>(null);
  const [messageInput, setMessageInput] = useState("");
  const [ruleInput, setRuleInput] = useState("");
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([]);
  const [loadingWorkspace, setLoadingWorkspace] = useState(true);
  const [submittingTurn, setSubmittingTurn] = useState(false);
  const [committingCheckpoint, setCommittingCheckpoint] = useState(false);
  const [revertingRevision, setRevertingRevision] = useState(false);
  const [workspaceSnapshots, setWorkspaceSnapshots] = useState<WorkspaceSnapshot[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [savingEntity, setSavingEntity] = useState(false);
  const [deletingEntity, setDeletingEntity] = useState(false);
  const [skillsCatalog, setSkillsCatalog] = useState<SkillDetail[]>([]);
  const [rulesCatalog, setRulesCatalog] = useState<RuleItem[]>([]);
  const [memoryFacts, setMemoryFacts] = useState<
    Array<{ id: number; key: string; value: unknown; type: string; confidence: number; updatedAt: string }>
  >([]);
  const [memorySummary, setMemorySummary] = useState("");
  const [memorySummaryVersion, setMemorySummaryVersion] = useState(0);
  const [memoryToasts, setMemoryToasts] = useState<Array<{ id: string; text: string }>>([]);
  const chatInputRef = useRef<HTMLInputElement | null>(null);
  const layoutRef = useRef<HTMLDivElement | null>(null);

  const orderedPanes = useMemo<PaneKey[]>(
    () => (["chats", "chat", "document", "documents"] as PaneKey[]).filter((pane) => paneVisibility[pane]),
    [paneVisibility],
  );
  const elasticPane = useMemo<PaneKey>(() => {
    if (paneVisibility.chat) return "chat";
    if (paneVisibility.document) return "document";
    return orderedPanes[0] ?? "chat";
  }, [orderedPanes, paneVisibility]);

  const sortedMessages = useMemo<ChatMessage[]>(
    () => [...(workspace?.messages ?? []), ...optimisticMessages],
    [workspace, optimisticMessages],
  );
  const docsByKey = useMemo<Record<string, { key: string; title: string; content: string; currentRevisionId: string | null }>>(
    () =>
      Object.fromEntries(
        (workspace?.documents ?? []).map((doc) => [doc.key, doc] as const),
      ),
    [workspace],
  );
  const explorerItemsByTab = useMemo<Record<ExplorerTab, ExplorerItem[]>>(
    () => ({
      documents: (workspace?.documents ?? []).map((doc) => ({
        id: doc.key,
        title: doc.title,
        subtitle: doc.key,
        entityType: "document",
      })),
      skills: skillsCatalog.map((skill) => ({
        id: skill.id,
        title: skill.name,
        subtitle: skill.brief,
        entityType: "skill",
      })),
      rules: rulesCatalog.map((rule) => ({
        id: String(rule.id),
        title: `Rule ${rule.id}`,
        subtitle: rule.ruleText,
        entityType: "rule",
      })),
      memories: [
        {
          id: "summary",
          title: `Summary v${memorySummaryVersion}`,
          subtitle: "Memory summary",
          entityType: "memory_summary",
        } satisfies ExplorerItem,
        ...memoryFacts.map((memory): ExplorerItem => ({
          id: String(memory.id),
          title: memory.key,
          subtitle: `${memory.type} · ${Math.round(memory.confidence * 100)}%`,
          entityType: "memory",
        })),
      ],
    }),
    [workspace?.documents, skillsCatalog, rulesCatalog, memoryFacts, memorySummaryVersion],
  );
  const activeDocumentKey = editorEntity?.entityType === "document" ? editorEntity.id : "";
  const activeDocument = activeDocumentKey ? docsByKey[activeDocumentKey] ?? null : null;

  const layoutColumns = useMemo(() => {
    if (orderedPanes.length <= 1) {
      return "minmax(0,1fr)";
    }
    const columns: string[] = [];
    for (let index = 0; index < orderedPanes.length; index += 1) {
      const pane = orderedPanes[index];
      if (pane === elasticPane) {
        columns.push(`minmax(${PANE_MIN[pane]}px,1fr)`);
      } else {
        columns.push(`minmax(${PANE_MIN[pane]}px,${Math.round(paneWidths[pane])}px)`);
      }
      if (index < orderedPanes.length - 1) {
        columns.push(`${SPLITTER_WIDTH}px`);
      }
    }
    return columns.join(" ");
  }, [orderedPanes, elasticPane, paneWidths]);

  const setPaneWidth = useCallback((pane: PaneKey, nextWidth: number): void => {
    const safe = Math.max(PANE_MIN[pane], Math.min(960, Math.round(nextWidth)));
    setPaneWidths((current) => ({ ...current, [pane]: safe }));
  }, []);

  function togglePane(pane: PaneKey): void {
    setPaneVisibility((current) => {
      const visibleCount = Object.values(current).filter(Boolean).length;
      if (current[pane] && visibleCount <= 1) return current;
      return { ...current, [pane]: !current[pane] };
    });
  }

  const loadWorkspace = useCallback(async (nextThreadId: string | null): Promise<void> => {
    setLoadingWorkspace(true);
    setError(null);
    try {
      const data = await copilotClient.getWorkspace(nextThreadId);
      setWorkspace(data);
      setThreadId(data.thread.id);
      setOptimisticMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspace.");
    } finally {
      setLoadingWorkspace(false);
    }
  }, []);

  const refreshExplorerData = useCallback(async (): Promise<void> => {
    const [skills, rules, memories] = await Promise.all([
      copilotClient.listSkills(),
      copilotClient.listRules(),
      copilotClient.listMemories(),
    ]);
    setSkillsCatalog(
      skills.skills.map((item) => ({
        id: item.id,
        name: item.name,
        brief: item.brief,
        prompt: "",
        enabled: item.enabled,
        allowedTools: item.allowedTools,
        requiredOrder: [],
        blockedCombinations: [],
      })),
    );
    setRulesCatalog(rules.rules);
    setMemoryFacts(memories.memories);
    setMemorySummary(memories.summary);
    setMemorySummaryVersion(memories.summaryVersion);
  }, []);

  const loadWorkspaceSnapshots = useCallback(async (): Promise<void> => {
    try {
      const response = await copilotClient.listWorkspaceSnapshots(80);
      setWorkspaceSnapshots(response.snapshots);
      setSelectedSnapshotId((current) => {
        if (current && response.snapshots.some((snapshot) => snapshot.id === current)) {
          return current;
        }
        return response.snapshots[0]?.id ?? "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workspace snapshots.");
    }
  }, []);

  async function onSubmitTurn(): Promise<void> {
    if (!threadId || !messageInput.trim() || submittingTurn) return;
    setSubmittingTurn(true);
    setError(null);
    const content = messageInput.trim();
    const nowIso = new Date().toISOString();
    const tempUserId = `tmp-user-${Date.now()}`;
    const tempAssistantId = `tmp-assistant-${Date.now()}`;
    setOptimisticMessages([
      { id: tempUserId, role: "user", content, createdAt: nowIso },
      {
        id: tempAssistantId,
        role: "assistant",
        content: "Thinking...",
        createdAt: nowIso,
        pending: true,
      },
    ]);
    try {
      await streamClient.streamChatTurn(threadId, content, {
        onCompleted: (payload) => {
          void loadWorkspace(payload.threadId);
        },
        onFailed: ({ error }) => {
          setError(error || "Failed to stream turn.");
        },
      });
      setMessageInput("");
    } catch (err) {
      const message =
        err instanceof BackendApiError
          ? err.errorCode
            ? `${err.message} [${err.errorCode}]`
            : err.message
          : err instanceof Error
            ? err.message
            : "Failed to submit turn.";
      setError(message);
    } finally {
      setSubmittingTurn(false);
    }
  }

  async function onCreateThread(): Promise<void> {
    try {
      const created = await copilotClient.createThread();
      await loadWorkspace(created.thread.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create thread.");
    }
  }

  useEffect(() => {
    const savedChatWidth = window.localStorage.getItem(STORAGE_CHAT_WIDTH);
    const savedChatPaneWidth = window.localStorage.getItem(STORAGE_CHAT_PANE_WIDTH);
    const savedDocWidth = window.localStorage.getItem(STORAGE_DOC_WIDTH);
    const savedDocsRailWidth = window.localStorage.getItem(STORAGE_DOCS_RAIL_WIDTH);
    const savedVisibility = window.localStorage.getItem(STORAGE_PANE_VISIBILITY);
    if (savedChatWidth) setPaneWidth("chats", Number(savedChatWidth));
    if (savedChatPaneWidth) setPaneWidth("chat", Number(savedChatPaneWidth));
    if (savedDocWidth) setPaneWidth("document", Number(savedDocWidth));
    if (savedDocsRailWidth) setPaneWidth("documents", Number(savedDocsRailWidth));
    if (savedVisibility) {
      try {
        const parsed = JSON.parse(savedVisibility) as Partial<PaneVisibility>;
        setPaneVisibility((current) => ({
          chats: parsed.chats ?? current.chats,
          chat: parsed.chat ?? current.chat,
          document: parsed.document ?? current.document,
          documents: parsed.documents ?? current.documents,
        }));
      } catch {
        // Ignore invalid visibility payloads.
      }
    }
    void Promise.all([loadWorkspace(null), refreshExplorerData(), loadWorkspaceSnapshots()]);
  }, [setPaneWidth, loadWorkspace, refreshExplorerData, loadWorkspaceSnapshots]);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_CHAT_WIDTH, String(Math.round(paneWidths.chats)));
    window.localStorage.setItem(STORAGE_CHAT_PANE_WIDTH, String(Math.round(paneWidths.chat)));
    window.localStorage.setItem(STORAGE_DOC_WIDTH, String(Math.round(paneWidths.document)));
    window.localStorage.setItem(STORAGE_DOCS_RAIL_WIDTH, String(Math.round(paneWidths.documents)));
  }, [paneWidths]);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_PANE_VISIBILITY, JSON.stringify(paneVisibility));
  }, [paneVisibility]);

  async function onSaveEditorEntity(): Promise<void> {
    if (!editorEntity || savingEntity) return;
    setSavingEntity(true);
    setError(null);
    try {
      if (editorEntity.entityType === "document") {
        await copilotClient.updateWorkingDocument(editorEntity.id, editorDraft);
        await loadWorkspace(threadId);
      } else if (editorEntity.entityType === "rule") {
        const payload = parseRuleMarkdown(editorDraft);
        await copilotClient.updateRule(Number(editorEntity.id), payload.ruleText);
        await refreshExplorerData();
      } else if (editorEntity.entityType === "memory") {
        const payload = parseMemoryMarkdown(editorDraft);
        await copilotClient.updateMemory(Number(editorEntity.id), payload);
        await refreshExplorerData();
      } else if (editorEntity.entityType === "memory_summary") {
        const payload = parseMemorySummaryMarkdown(editorDraft);
        const response = await copilotClient.updateMemorySummary(payload.summary);
        setMemorySummary(response.summary);
        setMemorySummaryVersion(response.summaryVersion);
        await refreshExplorerData();
      } else if (editorEntity.entityType === "skill") {
        const payload = parseSkillMarkdown(editorDraft);
        await copilotClient.updateSkill(editorEntity.id, payload);
        await refreshExplorerData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save item.");
    } finally {
      setSavingEntity(false);
    }
  }

  async function onCommitCheckpoint(): Promise<void> {
    if (committingCheckpoint) return;
    setCommittingCheckpoint(true);
    setError(null);
    try {
      await copilotClient.createWorkspaceSnapshot("Manual workspace snapshot");
      await Promise.all([loadWorkspace(threadId), loadWorkspaceSnapshots()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workspace snapshot.");
    } finally {
      setCommittingCheckpoint(false);
    }
  }

  async function onRestoreSnapshot(): Promise<void> {
    if (!selectedSnapshotId || revertingRevision) return;
    setRevertingRevision(true);
    setError(null);
    try {
      await copilotClient.restoreWorkspaceSnapshot(selectedSnapshotId, "Restore selected workspace snapshot");
      await Promise.all([loadWorkspace(threadId), refreshExplorerData(), loadWorkspaceSnapshots()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to restore workspace snapshot.");
    } finally {
      setRevertingRevision(false);
    }
  }

  async function onCreateDocument(): Promise<void> {
    const title = window.prompt("New document title");
    if (!title || !title.trim()) return;
    try {
      await copilotClient.createDocument(title.trim());
      await loadWorkspace(threadId);
      await refreshExplorerData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create document.");
    }
  }

  async function onAddRule(): Promise<void> {
    if (!ruleInput.trim()) return;
    try {
      await copilotClient.addRule(ruleInput.trim());
      setRuleInput("");
      await refreshExplorerData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add rule.");
    }
  }

  async function onDeleteEditorEntity(): Promise<void> {
    if (!editorEntity || deletingEntity) return;
    if (!window.confirm(`Delete ${editorEntity.entityType}:${editorEntity.id}? This cannot be undone.`)) return;
    setDeletingEntity(true);
    setError(null);
    try {
      if (editorEntity.entityType === "document") {
        await copilotClient.deleteDocument(editorEntity.id);
        await loadWorkspace(threadId);
      } else if (editorEntity.entityType === "rule") {
        await copilotClient.deleteRule(Number(editorEntity.id));
        await refreshExplorerData();
      } else if (editorEntity.entityType === "memory") {
        await copilotClient.deleteMemory(Number(editorEntity.id));
        await refreshExplorerData();
      } else if (editorEntity.entityType === "memory_summary") {
        await copilotClient.deleteMemorySummary();
        setMemorySummary("");
        setMemorySummaryVersion(0);
        await refreshExplorerData();
      } else if (editorEntity.entityType === "skill") {
        await copilotClient.deleteSkill(editorEntity.id);
        await refreshExplorerData();
      }
      setEditorEntity(null);
      setEditorDraft("");
      setActiveExplorerItemId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete item.");
    } finally {
      setDeletingEntity(false);
    }
  }

  const onSelectExplorerItem = useCallback(async (item: ExplorerItem): Promise<void> => {
    setActiveExplorerItemId(`${item.entityType}:${item.id}`);
    setError(null);
    try {
      if (item.entityType === "document") {
        const doc = docsByKey[item.id];
        if (!doc) {
          setError("Document not found in workspace.");
          return;
        }
        setEditorEntity({ entityType: "document", id: doc.key, title: doc.title });
        setEditorDraft(doc.content);
        return;
      }
      if (item.entityType === "rule") {
        const response = await copilotClient.getRule(Number(item.id));
        setEditorEntity({ entityType: "rule", id: item.id, title: `Rule ${item.id}` });
        setEditorDraft(toRuleMarkdown(response.rule));
        return;
      }
      if (item.entityType === "memory") {
        const response = await copilotClient.getMemory(Number(item.id));
        setEditorEntity({ entityType: "memory", id: item.id, title: response.memory.key });
        setEditorDraft(toMemoryMarkdown(response.memory));
        return;
      }
      if (item.entityType === "memory_summary") {
        setEditorEntity({ entityType: "memory_summary", id: "summary", title: "Memory Summary" });
        setEditorDraft(toMemorySummaryMarkdown(memorySummary));
        return;
      }
      if (item.entityType === "skill") {
        const response = await copilotClient.getSkill(item.id);
        setEditorEntity({ entityType: "skill", id: item.id, title: response.skill.name });
        setEditorDraft(toSkillMarkdown(response.skill));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open item.");
    }
  }, [docsByKey, memorySummary]);

  useEffect(() => {
    function onMouseMove(event: MouseEvent): void {
      if (!dragState || !layoutRef.current) return;
      const bounds = layoutRef.current.getBoundingClientRect();
      const deltaX = event.clientX - dragState.startX;
      const leftPane = dragState.leftPane;
      const rightPane = dragState.rightPane;
      const leftElastic = leftPane === elasticPane;
      const rightElastic = rightPane === elasticPane;
      if (leftElastic && !rightElastic) {
        setPaneWidth(rightPane, dragState.startRightWidth - deltaX);
        return;
      }
      if (rightElastic && !leftElastic) {
        setPaneWidth(leftPane, dragState.startLeftWidth + deltaX);
        return;
      }
      const tentativeLeft = dragState.startLeftWidth + deltaX;
      const maxLeft = bounds.width - PANE_MIN[rightPane] - SPLITTER_WIDTH;
      setPaneWidth(leftPane, Math.min(maxLeft, tentativeLeft));
    }

    function onMouseUp(): void {
      setDragState(null);
    }

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [dragState, elasticPane, setPaneWidth]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      if ((event.metaKey || event.ctrlKey) && event.key === "\\") {
        event.preventDefault();
        togglePane("documents");
      }
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === "1") {
        event.preventDefault();
        chatInputRef.current?.focus();
      }
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === "2") {
        event.preventDefault();
        setPaneVisibility((current) => ({ ...current, document: true, documents: true }));
        const firstDoc = explorerItemsByTab.documents[0];
        if (firstDoc) {
          void onSelectExplorerItem(firstDoc);
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [workspace, explorerItemsByTab.documents, onSelectExplorerItem]);

  useEffect(() => {
    if (!editorEntity) {
      const firstDoc = explorerItemsByTab.documents[0];
      if (firstDoc) {
        void onSelectExplorerItem(firstDoc);
      }
    }
  }, [editorEntity, explorerItemsByTab.documents, onSelectExplorerItem]);

  useEffect(() => {
    const userId = workspace?.userId;
    if (!userId) return;
    const unsubscribe = streamClient.subscribeNotifications(userId, {
      onMemoryWritten: (payload) => {
        const id = `${Date.now()}-${Math.random()}`;
        const text = `Memory saved: ${payload.memoryKey}`;
        setMemoryToasts((current) => [...current, { id, text }].slice(-4));
        window.setTimeout(() => {
          setMemoryToasts((current) => current.filter((item) => item.id !== id));
        }, 5000);
      },
    });
    return unsubscribe;
  }, [workspace?.userId]);

  return (
    <main className="h-screen w-full bg-stone-100/60 p-2 text-stone-900">
      <div className="mb-2 grid grid-cols-[1fr_auto_1fr] items-center gap-2 rounded-xl border border-stone-300/80 bg-background px-3 py-2 shadow-sm">
        <div className="text-xs text-muted-foreground">Drag pane boundaries to resize</div>
        <p className="text-base font-semibold tracking-tight">CFAI Workspace</p>
        <div className="flex items-center justify-end gap-1">
          <Button size="sm" variant={paneVisibility.chats ? "default" : "outline"} onClick={() => togglePane("chats")}>
            Chats
          </Button>
          <Button size="sm" variant={paneVisibility.chat ? "default" : "outline"} onClick={() => togglePane("chat")}>
            Chat
          </Button>
          <Button size="sm" variant={paneVisibility.document ? "default" : "outline"} onClick={() => togglePane("document")}>
            Document
          </Button>
          <Button size="sm" variant={paneVisibility.documents ? "default" : "outline"} onClick={() => togglePane("documents")}>
            Documents
          </Button>
        </div>
      </div>

      <div
        ref={layoutRef}
        className="grid h-[calc(100vh-4.5rem)] min-h-0 overflow-x-auto overflow-y-hidden rounded-xl border border-stone-300/80 bg-background shadow-sm"
        style={{ gridTemplateColumns: layoutColumns }}
      >
        {orderedPanes.map((pane, index) => {
          const nextPane = orderedPanes[index + 1];
          return (
            <div key={pane} className="contents">
              {pane === "chats" ? (
                <ChatsRail
                  threads={workspace?.threads ?? []}
                  activeThreadId={threadId}
                  onSelectThread={(nextThreadId) => void loadWorkspace(nextThreadId)}
                  onNewThread={() => void onCreateThread()}
                />
              ) : null}
              {pane === "chat" ? (
                <div className="flex min-h-0 flex-col border-r">
                  <ChatPane
                    messages={sortedMessages}
                    composerValue={messageInput}
                    submitting={submittingTurn}
                    onComposerChange={setMessageInput}
                    onSubmit={() => void onSubmitTurn()}
                    composerRef={chatInputRef}
                  />
                </div>
              ) : null}
              {pane === "document" ? (
                <DocPane
                  title={editorEntity?.title ?? ""}
                  entityType={editorEntity?.entityType ?? null}
                  entityId={editorEntity?.id ?? ""}
                  document={activeDocument}
                  draftContent={editorDraft}
                  saving={savingEntity}
                  deleting={deletingEntity}
                  canDelete={Boolean(editorEntity)}
                  onDraftChange={setEditorDraft}
                  onSave={() => void onSaveEditorEntity()}
                  onDelete={() => void onDeleteEditorEntity()}
                  onHide={() => togglePane("document")}
                />
              ) : null}
              {pane === "documents" ? (
                <DocsRail
                  activeTab={activeExplorerTab}
                  activeItemId={activeExplorerItemId}
                  itemsByTab={explorerItemsByTab}
                  onSelectTab={setActiveExplorerTab}
                  onSelectItem={(item) => void onSelectExplorerItem(item)}
                  onCreateDoc={() => void onCreateDocument()}
                  snapshots={workspaceSnapshots}
                  selectedSnapshotId={selectedSnapshotId}
                  committingSnapshot={committingCheckpoint}
                  restoringSnapshot={revertingRevision}
                  ruleInput={ruleInput}
                  rules={rulesCatalog.map((rule) => ({ id: rule.id, ruleText: rule.ruleText }))}
                  onRuleInputChange={setRuleInput}
                  onAddRule={() => void onAddRule()}
                  onCommitSnapshot={() => void onCommitCheckpoint()}
                  onSelectSnapshot={setSelectedSnapshotId}
                  onRestoreSnapshot={() => void onRestoreSnapshot()}
                  onHide={() => togglePane("documents")}
                />
              ) : null}

              {nextPane ? (
                <div
                  role="separator"
                  aria-orientation="vertical"
                  className="cursor-col-resize bg-stone-300/60 transition hover:bg-stone-400/80"
                  onMouseDown={(event) => {
                    setDragState({
                      leftPane: pane,
                      rightPane: nextPane,
                      startX: event.clientX,
                      startLeftWidth: paneWidths[pane],
                      startRightWidth: paneWidths[nextPane],
                    });
                  }}
                />
              ) : null}
            </div>
          );
        })}
      </div>

      {loadingWorkspace ? <p className="mt-2 text-xs text-muted-foreground">Loading workspace...</p> : null}
      {error ? (
        <Alert variant="destructive" className="mt-2 rounded-lg">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {memoryToasts.map((toast) => (
          <Alert key={toast.id} className="pointer-events-auto border-primary/40 bg-background shadow">
            <AlertTitle>Memory Updated</AlertTitle>
            <AlertDescription>{toast.text}</AlertDescription>
          </Alert>
        ))}
      </div>
    </main>
  );
}
