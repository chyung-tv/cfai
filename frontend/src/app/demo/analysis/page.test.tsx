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

  it("renders maintenance sections", () => {
    render(<AnalysisDemoPage />);

    expect(screen.getByText("Maintenance (Internal)")).toBeInTheDocument();
    expect(screen.getByText("Fetch")).toBeInTheDocument();
    expect(screen.getByText("Stock Catalogue")).toBeInTheDocument();
    expect(screen.getByText("Mass Update Analysis")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run Mass Update" })).toBeDisabled();
  });

  it("loads catalog, selects symbol, and runs mass update", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total: 1,
        stocks: [
          {
            symbol: "AAPL",
            nameDisplay: "Apple",
            sector: "Technology",
            marketCap: 1000,
            isActive: true,
            selectionRank: 1,
            updatedAt: "2026-03-11T00:00:00Z",
          },
        ],
      }),
    });
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        traceId: "trace-1",
      }),
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Load Catalogue" }));
    await userEvent.click(screen.getByLabelText("Select AAPL"));
    await userEvent.click(screen.getByRole("button", { name: "Run Mass Update" }));

    await screen.findByText("trace-1");
    expect(screen.getByText("succeeded")).toBeInTheDocument();
  });

  it("shows an error alert when catalog fetch fails", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<AnalysisDemoPage />);
    await userEvent.click(screen.getByRole("button", { name: "Load Catalogue" }));

    await waitFor(() => {
      expect(screen.getByText("Catalogue error")).toBeInTheDocument();
    });
    expect(screen.getByText("Catalog fetch failed (500)")).toBeInTheDocument();
  });
});
