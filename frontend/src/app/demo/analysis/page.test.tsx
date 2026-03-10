import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import AnalysisDemoPage from "./page";

const fullPayload = {
  summary: {
    investmentThesis: {
      text: "High-margin compounder with disciplined capital allocation.",
    },
    businessQuality: {
      tier: "A",
      subfactors: {
        moatStrength: "Strong ecosystem lock-in",
        managementExecution: "Consistently beats guidance",
        industryPositioning: "Category leader in premium segment",
      },
    },
    valuationLegitimacy: {
      label: "Legitimate",
      basis: "median required CAGR 11.2%, median likelihood likely",
    },
    analysisFreshness: {
      isFresh: true,
    },
  },
  details: {
    structuredOutput: {
      executiveSummary: {
        summary: "Fallback thesis text",
      },
    },
  },
};

describe("AnalysisDemoPage", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders summary-first cards from summary contract data", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => fullPayload,
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Refresh from DB" }));

    await screen.findByText("Legitimate");
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("High-margin compounder with disciplined capital allocation.")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Deep Research" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Quant" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Decision" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Raw" })).toBeInTheDocument();
  });

  it("shows explicit placeholders when summary fields are missing", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        summary: {
          investmentThesis: { text: null },
          businessQuality: { tier: null, subfactors: {} },
          valuationLegitimacy: { label: null, basis: null },
          analysisFreshness: { isFresh: null },
        },
        details: {},
      }),
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Refresh from DB" }));

    await screen.findAllByText("Unavailable in current payload");
    expect(screen.getAllByText("Partial").length).toBeGreaterThan(0);
  });

  it("keeps drill-down navigation visible through loading transitions", async () => {
    let resolveFetch: ((value: { ok: boolean; json: () => Promise<unknown> }) => void) | null = null;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
    );

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Refresh from DB" }));

    expect(screen.getByRole("button", { name: "Loading..." })).toBeDisabled();
    expect(screen.getByRole("tab", { name: "Deep Research" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Quant" })).toBeInTheDocument();

    resolveFetch?.({
      ok: true,
      json: async () => fullPayload,
    });

    await screen.findByText("Legitimate");
  });

  it("shows an error alert while keeping summary and tabs stable", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Refresh from DB" }));

    await waitFor(() => {
      expect(screen.getByText("Analysis error")).toBeInTheDocument();
    });
    expect(screen.getByRole("tab", { name: "Deep Research" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Decision" })).toBeInTheDocument();
    expect(screen.getByText("Summary Cards")).toBeInTheDocument();
  });
});
