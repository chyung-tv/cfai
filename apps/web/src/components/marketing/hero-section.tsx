"use client";

import { StockSearchBar } from "@/components/shared/stock-search-bar";

interface HeroSectionProps {
  onAnalyze?: (symbol: string) => void;
}

export function HeroSection({ onAnalyze }: HeroSectionProps) {
  return (
    <section className="container mx-auto px-4 py-20 text-center">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight bg-linear-to-r from-slate-900 via-blue-800 to-indigo-900 dark:from-slate-100 dark:via-blue-200 dark:to-indigo-200 bg-clip-text text-transparent">
            AI-Powered Stock Valuation Analysis
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Deep qualitative analysis meets rigorous DCF modeling. Understand
            business quality, valuation reality, and market-implied growth
            assumptions—all in one comprehensive report.
          </p>
        </div>

        <StockSearchBar variant="hero" onSearch={onAnalyze} />
      </div>
    </section>
  );
}
