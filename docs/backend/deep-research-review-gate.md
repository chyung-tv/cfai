# Deep Research Review Gate (No Live Run)

This document is the preflight contract for the deep-research node.  
No production inference should be executed until this is approved.

Reference: Gemini Deep Research Agent docs  
`https://ai.google.dev/gemini-api/docs/deep-research`

## 1) Prompt Template Source

- Runtime builder: `backend/app/workflow/prompts/deep_research_prompt.py`
- Node usage: `backend/app/workflow/nodes/deep_research.py`

The runtime prompt includes:
- CFA-style persona and rigor constraints
- fixed section order matching target report quality
- source-priority policy (SEC > IR > trusted financial press)
- explicit citation and methodology transparency requirements
- markdown output contract with Works Cited

## 2) Exact SDK Call Shape (Planned)

The provider wrapper performs:

1) Create interaction (background):

```python
interaction = client.interactions.create(
    input=prompt,
    agent=agent_name,  # default: deep-research-pro-preview-12-2025
    background=True,
    store=True,
)
```

2) Poll interaction:

```python
current = client.interactions.get(interaction_id)
status = current.status  # expected: in_progress/completed/failed
```

3) Completion extraction:

```python
report_markdown = current.outputs[-1].text
```

## 3) Runtime Controls

Configured via `backend/app/core/config.py`:

- `GOOGLE_API_KEY`
- `DEEP_RESEARCH_AGENT` (default: `deep-research-pro-preview-12-2025`)
- `DEEP_RESEARCH_POLL_INTERVAL_SECONDS` (default: `10`)
- `DEEP_RESEARCH_MAX_WAIT_SECONDS` (default: `1200`)
- `DEEP_RESEARCH_ENABLE_LIVE_CALLS` (default: `false`)

## 4) Safety Gate

`DEEP_RESEARCH_ENABLE_LIVE_CALLS=false` keeps the provider in dry-run mode.

Dry-run behavior:
- no external Gemini call is made
- workflow completes with a deterministic placeholder message indicating live calls are disabled

## 5) Expected Persisted Result Shape

Stored in `analysis_workflows.result_payload`:

- `reportMarkdown`: full report markdown
- `citations`: normalized citation list
- `interactionId`: deep-research interaction id
- `generatedAt`: ISO timestamp
- `modelMetadata`: agent/mode metadata

## 6) Sign-off Checklist

Before first live run, confirm:

1. Prompt content and section order are approved.
2. Agent name and polling limits are approved.
3. Cost/latency expectation is accepted.
4. `DEEP_RESEARCH_ENABLE_LIVE_CALLS` remains `false` until final go-ahead.
