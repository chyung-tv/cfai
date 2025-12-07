import { BusinessQualityCard } from "@/components/analysis/business-quality-card";
import { AllocationCard } from "@/components/analysis/allocation-card";
import { SensitivityTable } from "@/components/analysis/sensitivity-table";
import { FeasibilityGauge } from "@/components/analysis/feasibility-gauge";
import { StrategicAnalysis } from "@/components/analysis/strategic-analysis";
import { AnalysisLoading } from "@/components/analysis/analysis-loading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, Share2 } from "lucide-react";
import { getAnalysis } from "@/lib/actions/analysis";
import { RefreshAnalysisButton } from "@/components/analysis/refresh-analysis-button";
import { auth, getUserAccess } from "@/lib/auth";
import { redirect } from "next/navigation";

interface AnalysisPageProps {
  params: Promise<{ ticker: string }>;
}

export default async function AnalysisPage({ params }: AnalysisPageProps) {
  const { ticker } = await params;
  const symbol = ticker.toUpperCase();

  // Fetch actual analysis data from database
  const analysisData = await getAnalysis(ticker);

  // If no data exists, check access before triggering analysis
  if (!analysisData) {
    const session = await auth();
    const hasAccess = getUserAccess(session);

    // No cache hit + no access = redirect to no-access page
    if (!hasAccess) {
      redirect("/dashboard/no-access");
    }

    // Has access, show loading component which will trigger analysis
    return (
      <>
        <div className="border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {symbol}
                </h1>
                <Badge className="bg-yellow-500 hover:bg-yellow-600 text-white">
                  Analyzing...
                </Badge>
              </div>
            </div>
          </div>
        </div>
        <section className="container mx-auto px-4 py-16">
          <AnalysisLoading ticker={ticker} />
        </section>
      </>
    );
  }

  // Cache hit - show analysis to everyone (even no-access users)
  // Extract data from analysis result
  const currentPrice = analysisData.price;
  const thesis = analysisData.thesis;
  const { dcf, rating } = analysisData;

  // Scenarios come from growth judgement embedded in dcf
  const feasibilityScenarios = dcf.scenarios || [];
  const independentPrediction = dcf.independentPrediction?.predictedCagr || 0;

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
              {/* <RefreshAnalysisButton ticker={ticker} /> */}
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
          <div className="mt-3 px-1">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              ℹ️ AI analysis is subjective and may produce different results on
              each run. Re-run to get a fresh perspective.
            </p>
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
              tier={rating?.tier.classification || "unknown"}
              moat={rating?.economicMoat.primaryMoat || "unknown"}
              marketStructure={rating?.marketStructure.structure || "unknown"}
              explanation={
                rating?.economicMoat.reason || "Analysis in progress"
              }
            />

            <FeasibilityGauge
              scenarios={feasibilityScenarios}
              independentPrediction={independentPrediction}
              currentPrice={currentPrice}
            />
          </div>

          {/* Row 2: Strategic Deep Dive */}
          <StrategicAnalysis thesis={thesis} />

          {/* Row 3: Action */}
          <AllocationCard
            recommendation={rating?.action.recommendation || "hold"}
            portfolioRole={
              rating?.portfolioFunction.primaryFunction || "speculation"
            }
            riskProfile={rating?.portfolioFunction.riskProfile || "moderate"}
            allocation={rating?.action.targetAllocation || 0}
            reasoning={rating?.action.reason || "Analysis in progress"}
          />

          {/* Row 4: Sensitivity */}
          <SensitivityTable
            currentPrice={currentPrice}
            sensitivity={dcf.sensitivity}
            usedDiscountRate={dcf.usedDiscountRate}
          />
        </div>
      </section>
    </>
  );
}
