import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AnalysisDemoPage from "./page";

describe("AnalysisDemoPage", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders internal-lab controls and badges", () => {
    render(<AnalysisDemoPage />);

    expect(screen.getByText("Analysis Observation Lab (Internal)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trigger Workflow" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh from DB" })).toBeInTheDocument();
    expect(screen.getByText("idle")).toBeInTheDocument();
    expect(screen.getByText("Freshness unknown")).toBeInTheDocument();
  });

  it("shows loaded status and freshness badge on successful refresh", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        summary: {
          analysisFreshness: {
            isFresh: true,
          },
        },
      }),
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Refresh from DB" }));

    await screen.findByText("completed_cached / latest_loaded");
    expect(screen.getByText("Fresh (<=7d)")).toBeInTheDocument();
  });

  it("shows an error alert when refresh fails", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Refresh from DB" }));

    await waitFor(() => {
      expect(screen.getByText("Analysis error")).toBeInTheDocument();
    });
    expect(screen.getByText("failed / latest_fetch_failed")).toBeInTheDocument();
  });
});
