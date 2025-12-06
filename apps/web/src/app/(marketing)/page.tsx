import { Header } from "@/components/marketing/header";
import { HeroSection } from "@/components/marketing/hero-section";
import { Footer } from "@/components/marketing/footer";
import { BusinessQualityCard } from "@/components/analysis/business-quality-card";
import { AllocationCard } from "@/components/analysis/allocation-card";
import { SensitivityTable } from "@/components/analysis/sensitivity-table";
import { FeasibilityGauge } from "@/components/analysis/feasibility-gauge";

export default function Home() {
  // Mock current market values
  const currentPrice = 150;

  // Mock Feasibility Data (Demo)
  const feasibilityScenarios = [
    {
      discountRate: 0.06,
      impliedGrowth: 0.042,
      feasibility: "VERY_HIGH" as const,
      gapAnalysis:
        "Implied growth of 4.2% is significantly below our predicted 8% baseline. The company can easily exceed this even in a bear case scenario.",
    },
    {
      discountRate: 0.07,
      impliedGrowth: 0.065,
      feasibility: "HIGH" as const,
      gapAnalysis:
        "Implied growth of 6.5% is comfortably achievable given the strong services segment tailwinds and recurring revenue base.",
    },
    {
      discountRate: 0.08,
      impliedGrowth: 0.088,
      feasibility: "MEDIUM" as const,
      gapAnalysis:
        "Implied growth of 8.8% aligns closely with our base case. This represents fair value for an investor seeking an 8% return.",
    },
    {
      discountRate: 0.09,
      impliedGrowth: 0.115,
      feasibility: "LOW" as const,
      gapAnalysis:
        "Implied growth of 11.5% is aggressive. It would require a successful launch of a major new product category (e.g., AR/VR) which is not guaranteed.",
    },
    {
      discountRate: 0.1,
      impliedGrowth: 0.148,
      feasibility: "VERY_LOW" as const,
      gapAnalysis:
        "Implied growth of 14.8% is highly optimistic. It exceeds the company's historical 5-year average and ignores saturation risks in the hardware market.",
    },
  ];

  // Mock DCF sensitivity data for demo
  const mockSensitivity = {
    terminalGrowthRates: [0.025, 0.0275, 0.03, 0.0325, 0.035],
    discountRates: [0.08, 0.085, 0.09, 0.095, 0.1],
    values: [
      [197.74, 204.13, 211.16, 218.93, 227.56],
      [180.06, 185.19, 190.78, 196.91, 203.65],
      [165.12, 169.3, 173.83, 178.75, 184.12],
      [152.34, 155.79, 159.51, 163.52, 167.86],
      [141.29, 144.17, 147.25, 150.56, 154.13],
    ],
  };

  const usedDiscountRate = 0.09; // Base case is 9%

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
              A comprehensive analysis of AAPL (Demo Data)
            </p>
          </div>

          {/* Row 1: Quality & Valuation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <BusinessQualityCard
              tier="strong_moat"
              moat="network_effect"
              marketStructure="global_monopoly"
              explanation="The company benefits from a powerful network effect where each new user adds value to the existing ecosystem. This creates high switching costs and barriers to entry for competitors, securing long-term profitability."
            />

            <FeasibilityGauge
              scenarios={feasibilityScenarios}
              independentPrediction={0.08}
              currentPrice={currentPrice}
            />
          </div>

          {/* Row 2: Action */}
          <AllocationCard
            recommendation="accumulate"
            portfolioRole="growth_and_income"
            riskProfile="moderate"
            allocation={5}
            reasoning="Given the strong moat and fair valuation (8% implied growth vs 8% predicted), this stock offers a balanced risk-reward profile. It serves as a core portfolio holding providing both capital appreciation and steady dividend growth."
          />

          {/* Row 3: Sensitivity */}
          <SensitivityTable
            currentPrice={currentPrice}
            sensitivity={mockSensitivity}
            usedDiscountRate={usedDiscountRate}
          />
        </div>
      </section>

      <Footer />
    </div>
  );
}
