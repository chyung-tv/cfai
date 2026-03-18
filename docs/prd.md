Product Requirements Document (PRD): AI Portfolio Co-Pilot & Co-Editing Canvas

1. Product Vision & Executive Summary

Product Name: Portfolio Co-Pilot Canvas
Objective: Create an immersive, collaborative workspace where a user and an autonomous AI agent manage an investment portfolio together. Instead of a rigid trading bot, this product is an Agentic Co-Editing Experience. The system centers around a canonical portfolio document (the "Canvas"). The agent acts as a deeply knowledgeable research analyst—investigating assets, proposing strategies, debating thesis points with the user, and physically co-editing the portfolio ledger and strategy journal as consensus is reached.

2. Core UX Paradigm: The Co-Editing Workspace

The application UI is fundamentally a split-screen collaborative environment:

Left Pane (The Conversational Interface): Where the user and agent converse. The agent presents deep research findings, alerts the user to macroeconomic headwinds, and discusses potential trades.

Right Pane (The Canonical Documents): The live, editable files (e.g., Markdown, CSV, or JSON tables). This includes the Portfolio Constitution (the numbers) and the Strategy Journal (the logic). Both the user and the agent have read/write access to these documents.

3. Agent Architecture: Memory Components

To function as a true co-pilot, the agent relies on a sophisticated, multi-layered memory system rather than just a context window.

State Memory (The Canonical Ledger): The live document acting as the ultimate source of truth for the portfolio's current constitution, weights, and asset tiers.

Alpha Memory (The Strategy Journal): A persistent document that stores the reasoning behind past decisions. The agent reads this to ensure it doesn't contradict established portfolio philosophy (e.g., "Remember, we agreed not to buy POOL because of terminal growth saturation").

Contextual Memory (Vector DB/Thread): Short-term conversational context and raw data ingested during the current session (e.g., OCR data from uploaded broker screenshots).

Philosophy Memory (Dynamic Ruleset): A flexible repository of user-defined rules created on the fly during conversations (e.g., the "Tier 1.5 Leg-in Rule" or the "18% Yield Safety Threshold").

4. Agent Skills, Scripting Engines & APIs

The agent is equipped with modular "skills." Each skill is explicitly wired to underlying scripts, programming engines, or external APIs to execute complex quantitative and qualitative tasks autonomously:

Deep Research & Discovery Skill:

Underlying Engine: Google Deep Research API.

Function: The ability to autonomously browse the web, pull live financial reports, read 10-Ks, and synthesize massive amounts of unstructured data to find hidden risks or catalysts (e.g., discovering the auditor warning for EchoStar).

Financial Modeling Skill (DCF & Reverse DCF):

Underlying Engine: Python Code Execution / Financial Scripting Engine.

Function: * Standard DCF: Calculates intrinsic value based on user-supplied or agent-researched parameters (e.g., terminal growth rates, WACC, operating margins).

Reverse DCF: Calculates the exact growth rate and margin assumptions currently priced into a stock's market value. This enables the agent to debate market expectations (e.g., "To justify this price, the market assumes 12% perpetual growth. Based on our research, the industry caps out at 3.5%.").

Qualitative Moat Analysis Skill:

Underlying Engine: LLM Reasoning & Strategy Prompting.

Function: The ability to debate qualitative business models, comparing structural advantages (e.g., "CapEx as a moat for Amazon" vs. "Network effects for Copart").

Canvas Manipulation Skill:

Underlying Engine: Markdown/JSON AST Parser & Math Evaluator.

Function: The precise ability to physically edit the canonical documents—calculating new percentages, inserting [PENDING BUY] flags, and formatting tables cleanly without hallucinating math or corrupting surrounding text.

Data Ingestion Skill:

Underlying Engine: Vision-Language Model (VLM) / OCR Engine.

Function: OCR capabilities to read user-uploaded screenshots of brokerage accounts and structure them accurately into the canonical document.

5. The Collaborative Workflow Loop

The interaction between the user and the agent follows a fluid, co-editing loop:

Ingestion & Structuring: User uploads current holdings (CSV/Image). The agent initializes the Canonical Document.

Research & Surfacing: Agent triggers the Google Deep Research API to run background checks on holdings. It might interject: "I noticed your SATS bond is yielding 42%. I ran a deep research task and found a 'going concern' warning. We should discuss this."

Deliberation (The Reverse DCF): User and agent debate an asset like POOL. The agent runs a Python script to execute a Reverse DCF, proving the market's growth expectations are mathematically unrealistic.

Consensus & Trade Routing: User asks to swap a distressed asset for a new one. The agent calculates the leverage impact to ensure margin rules are respected.

Co-Editing Execution: Once the user approves the logic, the agent's Canvas Manipulation Skill actively edits the Canonical Document (updating weights) and appends the reasoning to the Strategy Journal.

6. Success Metrics / Acceptance Criteria

Co-Editing Fidelity: The agent must be able to edit specific rows and columns in the canonical document without breaking the formatting or corrupting surrounding data.

Rule Adaptability: The agent must seamlessly adopt new rules invented by the user mid-conversation and apply them to all future analyses in that session.

Research Accuracy: Financial data retrieved by the Deep Research API must be grounded and hallucination-free.

Math Consistency: Reverse DCF calculations and portfolio weight changes initiated by the agent's scripts must sum correctly and reflect the user's targeted leverage constraints.