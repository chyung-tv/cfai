import { BusinessQualityCard } from "@/components/analysis/business-quality-card";
import { AllocationCard } from "@/components/analysis/allocation-card";
import { SensitivityTable } from "@/components/analysis/sensitivity-table";
import { FeasibilityGauge } from "@/components/analysis/feasibility-gauge";
import { StrategicAnalysis } from "@/components/analysis/strategic-analysis";
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

  // Mock Thesis Data
  const mockThesis = {
    executiveSummary:
      "The company maintains a dominant market position driven by its integrated ecosystem and brand loyalty. While hardware sales face saturation, services revenue is accelerating, driving margin expansion. The stock appears fairly valued relative to its high-quality cash flows.",
    businessProfile: {
      essence:
        "A global technology leader designing consumer electronics, software, and services. Core value prop lies in the seamless integration of hardware (iPhone, Mac) with services (iCloud, App Store).",
      moat: "The ecosystem creates high switching costs. Once a user owns multiple devices and subscribes to services, leaving the platform becomes expensive and inconvenient. This 'walled garden' is the primary source of pricing power.",
    },
    porter: {
      threatOfEntrants:
        "Low. High capital requirements, massive brand loyalty, and established supply chains make it nearly impossible for new entrants to compete at scale.",
      bargainingPowerSuppliers:
        "Moderate. While the company relies on key chip manufacturers, its massive order volume gives it significant leverage to negotiate favorable terms.",
      bargainingPowerBuyers:
        "Low to Moderate. Individual consumers have little power, but the premium pricing strategy makes demand sensitive to macroeconomic downturns.",
      threatOfSubstitutes:
        "Moderate. Android devices offer similar functionality at lower prices, but the brand cachet and ecosystem lock-in mitigate this threat.",
      competitiveRivalry:
        "High. Intense competition from other tech giants in smartphones, cloud services, and streaming media.",
    },
    drivers: {
      externalTailwinds:
        "Growing demand for wearables and health-tech. Expansion of 5G networks driving device upgrades.",
      externalHeadwinds:
        "Geopolitical tensions affecting supply chains. Regulatory scrutiny over App Store practices in the EU and US.",
      internalCatalysts:
        "Transition to proprietary silicon chips improving margins and performance. Growth of high-margin services segment.",
      internalDrags:
        "Slowing innovation cycles in the smartphone category. Dependence on a single product line for a large portion of revenue.",
    },
    managementProfile: {
      leadership:
        "Led by a veteran CEO known for operational excellence and supply chain mastery. The executive team has a long tenure and deep industry experience.",
      compensationAlignment:
        "Executive compensation is heavily weighted towards performance-based stock awards, aligning management interests with long-term shareholder value.",
    },
    industryProfile: {
      growthProjections: 0.05,
      trends:
        "Shift towards services and recurring revenue models. Increasing focus on privacy and data security.",
      competition:
        "The market is an oligopoly dominated by a few large players. Market share is stable, with competition shifting from hardware specs to ecosystem features.",
    },
    recentDevelopments:
      "Recently announced a new mixed-reality headset, marking entry into a new product category. Quarterly earnings beat expectations driven by record services revenue.",
  };

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

          {/* Row 2: Strategic Deep Dive */}
          <StrategicAnalysis thesis={mockThesis} />

          {/* Row 3: Action */}
          <AllocationCard
            recommendation="accumulate"
            portfolioRole="growth_and_income"
            riskProfile="moderate"
            allocation={5}
            reasoning="Given the strong moat and fair valuation (8% implied growth vs 8% predicted), this stock offers a balanced risk-reward profile. It serves as a core portfolio holding providing both capital appreciation and steady dividend growth."
          />

          {/* Row 4: Sensitivity */}
          <SensitivityTable
            currentPrice={currentPrice}
            calculatePrice={calculatePrice}
          />
        </div>
      </section>
    </>
  );
}
