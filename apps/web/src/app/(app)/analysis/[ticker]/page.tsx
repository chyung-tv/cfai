import { VerdictCard } from "@/components/analysis/verdict-card";
import { GapAnalysisCard } from "@/components/analysis/gap-analysis-card";
import { DCFMetricsCard } from "@/components/analysis/dcf-metrics-card";
import { SensitivityTable } from "@/components/analysis/sensitivity-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, Share2 } from "lucide-react";

interface AnalysisPageProps {
  params: Promise<{ ticker: string }>;
}

export default async function AnalysisPage({ params }: AnalysisPageProps) {
  const { ticker } = await params;
  const symbol = ticker.toUpperCase();

  // TODO: Fetch actual analysis data from backend API
  // const response = await fetch(`http://localhost:3001/stock/search?symbol=${symbol}`);
  // const data = await response.json();

  // Mock data for now (same as marketing page)
  const currentPrice = 150;
  const impliedGrowth = 18;
  const marketDiscountRate = 10;

  const calculatePrice = (growth: number, discount: number) => {
    const base = 100;
    const factor = (1 + growth / 100) / (discount / 100);
    return Math.round(base * factor);
  };

  return (
    <>
      {/* Page Header */}
      <div className="border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {symbol}
              </h1>
              <Badge className="bg-green-500 hover:bg-green-600 text-white">
                Analyzed
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto space-y-12">
          {/* Title Section */}
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              Analysis Report
            </h2>
            <p className="text-slate-600 dark:text-slate-400">
              Comprehensive AI-powered stock analysis for {symbol}
            </p>
          </div>

          {/* Analysis Cards */}
          <VerdictCard
            verdict="Possible"
            explanation="The current market price reflects optimistic growth expectations. While this stock has strong fundamentals, the pricing assumes near-perfect execution in a competitive landscape with margin pressures from supply chain constraints and emerging competitors in key markets."
          />

          <GapAnalysisCard
            marketExpects={18}
            aiPredicts="12-14% Growth"
            rationale="Market is pricing in a perfection scenario, but competition in the sector suggests margins will contract by 2-3%. Historical data shows that during similar market conditions, growth rates stabilize around 12-15%."
          />

          <DCFMetricsCard
            currentPrice={currentPrice}
            impliedGrowth={impliedGrowth}
            discountRate={marketDiscountRate}
            isDiscountRateEditable
          />

          <SensitivityTable
            currentPrice={currentPrice}
            calculatePrice={calculatePrice}
          />
        </div>
      </section>
    </>
  );
}
