System Architecture Blueprint: AI Portfolio Co-Pilot

This blueprint defines the modular architecture for the Portfolio Co-Pilot Canvas, mapping the capabilities defined in the PRD to specific technologies and infrastructure.

Module 1: The Co-Editing Client (Frontend Layer)

Purpose: Handles the split-screen UI, real-time chat, and the collaborative document editing experience.

Core Framework: Next.js (React) * Why: Industry standard for fast, stateful AI applications.

Chat & Streaming UI: Vercel AI SDK

Why: Simplifies streaming text and dynamic UI components (Generative UI) from the backend to the chat pane.

Canvas Editor: TipTap (or ProseMirror)

Why: A headless rich-text editor that allows the AI to programmatically inject Markdown (like updating the ledger tables) without disrupting the user's manual edits.

Styling: Tailwind CSS

Module 2: The Agent Orchestrator (Logic Layer)

Purpose: The "brain" of the operation. Routes user intents, manages the state of the conversation, and decides which skills to use.

Backend Framework: FastAPI (Python)

Why: Python is essential for financial engineering and data science libraries. FastAPI is lightweight and asynchronous.

Agent Framework: LangGraph

Why: Manages the agent's workflow as a strict state machine (Ingest → Research → Deliberate → Edit), preventing infinite loops and ensuring adherence to the Master Operating Procedures (MOP).

Core LLM: Google Gemini 2.5 Pro (or Anthropic Claude 3.5 Sonnet)

Why: Best-in-class at complex reasoning, Python code generation, and strict formatting adherence for document editing.

Module 3: Memory & Persistence (Data Layer)

Purpose: Stores the canonical documents, conversation history, and dynamic rulesets.

Primary Database: PostgreSQL (via Supabase)

Why: Relational database perfect for storing user profiles, portfolio snapshots, and the raw markdown strings of the Canonical Ledger and Strategy Journal.

Vector Database (Contextual Memory): pgvector (within Supabase)

Why: Stores embedded conversation history and unstructured research data, allowing the agent to "remember" why a stock was categorized a certain way three weeks ago.

Module 4: Agent Skills & Execution Sandbox (Tooling Layer)

Purpose: The external APIs and sandboxes the agent connects to when it needs to perform deep research or complex math.

Financial Modeling (DCF) Engine: E2B (e2b.dev)

Why: A secure, cloud-based Python sandbox. The agent writes DCF/Reverse DCF scripts and runs them here safely to get mathematical answers, completely eliminating math hallucinations.

Deep Research Skill: Google Deep Research API + Tavily/Firecrawl

Why: Allows the agent to autonomously scrape the web, read 10-K SEC filings, and synthesize news events (like auditor warnings).

Live Financial Data API: Financial Modeling Prep (FMP) or Alpha Vantage

Why: Provides the live ticker prices, OTC bond yields, and historical CAGR data needed to evaluate Tier 1/2 discounts.

Module 5: Data Ingestion (Integration Layer)

Purpose: How the system gets portfolio data from the real world into the Canvas.

OCR & Vision Engine: Gemini Vision (Native multimodality)

Why: Parses uploaded brokerage screenshots (like Interactive Brokers) to extract tickers, weights, and yields.

Direct Broker Integration (V2 Phase): Plaid or Interactive Brokers API

Why: For the future roadmap, allowing real-time, automated syncing of margin utilization and portfolio weights without needing screenshots.

Architectural Flow Diagram (The Request Cycle)

User Request: User types "Swap INTU for OTIS" in the Next.js UI.

Orchestration: FastAPI receives the prompt. LangGraph routes it to the LLM.

Execution: The LLM uses the FMP API to check OTIS's current discount. It uses E2B to calculate the exact portfolio weight changes needed to maintain 100% leverage.

State Update: The LLM generates the Markdown diff. Supabase is updated.

UI Refresh: Vercel AI SDK streams the chat response and TipTap updates the live Canvas.