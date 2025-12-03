import { Header } from "@/components/marketing/header";
import { HeroSection } from "@/components/marketing/hero-section";
import { Footer } from "@/components/marketing/footer";
import { VerdictCard } from "@/components/analysis/verdict-card";
import { GapAnalysisCard } from "@/components/analysis/gap-analysis-card";
import { DCFMetricsCard } from "@/components/analysis/dcf-metrics-card";
import { SensitivityTable } from "@/components/analysis/sensitivity-table";

export default function Home() {
  // Mock current market values
  const currentPrice = 150;
  const impliedGrowth = 18;
  const marketDiscountRate = 10;

  // Function to calculate share price based on growth and discount rate
  const calculatePrice = (growth: number, discount: number) => {
    // Simplified mock calculation
    const base = 100;
    const factor = (1 + growth / 100) / (discount / 100);
    return Math.round(base * factor);
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <Header />
      <HeroSection />

      {/* Feature Showcase */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              What You Get
            </h2>
            <p className="text-slate-600 dark:text-slate-400">
              A comprehensive analysis of AAPL (Example)
            </p>
          </div>

          <VerdictCard
            verdict="Possible"
            explanation="The current market price reflects optimistic growth expectations. While AAPL has strong fundamentals, the pricing assumes near-perfect execution in a competitive landscape with margin pressures from supply chain constraints and emerging competitors in key markets."
          />

          <GapAnalysisCard
            marketExpects={18}
            aiPredicts="12-14% Growth"
            rationale="Market is pricing in a perfection scenario, but competition in the smartphone and services sectors suggests margins will contract by 2-3%. Historical data shows that during similar market conditions, growth rates stabilize around 12-15%."
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

      <Footer />
    </div>
  );
}
