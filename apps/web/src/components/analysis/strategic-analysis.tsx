import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  TrendingDown,
  Zap,
  Anchor,
  Users,
  Briefcase,
  Globe,
  AlertTriangle,
} from "lucide-react";

// Define the schema interface based on parseThesis.ts
export interface StructuredThesis {
  executiveSummary: string;
  businessProfile: {
    essence: string;
    moat: string;
  };
  porter: {
    threatOfEntrants: string;
    bargainingPowerSuppliers: string;
    bargainingPowerBuyers: string;
    threatOfSubstitutes: string;
    competitiveRivalry: string;
  };
  drivers: {
    externalTailwinds: string;
    externalHeadwinds: string;
    internalCatalysts: string;
    internalDrags: string;
  };
  managementProfile: {
    leadership: string;
    compensationAlignment: string;
  };
  industryProfile: {
    growthProjections: number;
    trends: string;
    competition: string;
  };
  recentDevelopments: string;
}

interface StrategicAnalysisProps {
  thesis: StructuredThesis;
}

export function StrategicAnalysis({ thesis }: StrategicAnalysisProps) {
  return (
    <Card className="w-full border-2 shadow-sm">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center gap-2">
          <Briefcase className="h-6 w-6 text-slate-600 dark:text-slate-400" />
          Strategic Deep Dive
        </CardTitle>
        <CardDescription>
          Comprehensive qualitative assessment of business model, industry, and
          management.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="summary" className="w-full">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5 h-auto">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="business">Business & Moat</TabsTrigger>
            <TabsTrigger value="industry">Industry</TabsTrigger>
            <TabsTrigger value="drivers">Drivers</TabsTrigger>
            <TabsTrigger value="management">Management</TabsTrigger>
          </TabsList>

          {/* 1. Executive Summary */}
          <TabsContent value="summary" className="space-y-6 mt-6">
            <div className="prose dark:prose-invert max-w-none">
              <h3 className="text-lg font-semibold mb-2">Executive Summary</h3>
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                {thesis.executiveSummary}
              </p>
            </div>

            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-100 dark:border-blue-900">
              <h4 className="flex items-center gap-2 font-semibold text-blue-800 dark:text-blue-300 mb-2">
                <Zap className="h-4 w-4" /> Recent Developments
              </h4>
              <p className="text-sm text-blue-900 dark:text-blue-200">
                {thesis.recentDevelopments}
              </p>
            </div>
          </TabsContent>

          {/* 2. Business & Moat */}
          <TabsContent value="business" className="space-y-6 mt-6">
            <div className="grid gap-6">
              <div className="space-y-2">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Globe className="h-5 w-5 text-slate-500" /> Business Essence
                </h3>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                  {thesis.businessProfile.essence}
                </p>
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Anchor className="h-5 w-5 text-emerald-500" /> Moat
                  Durability
                </h3>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                  {thesis.businessProfile.moat}
                </p>
              </div>
            </div>
          </TabsContent>

          {/* 3. Industry & Competition (Porter) */}
          <TabsContent value="industry" className="space-y-8 mt-6">
            {/* Industry Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-slate-50 dark:bg-slate-900 border-none">
                <CardContent className="pt-6">
                  <div className="text-sm text-slate-500 font-medium uppercase">
                    Proj. Industry CAGR
                  </div>
                  <div className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                    {(thesis.industryProfile.growthProjections * 100).toFixed(
                      1
                    )}
                    %
                  </div>
                </CardContent>
              </Card>
              <div className="md:col-span-2 space-y-4">
                <div>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                    Key Trends:{" "}
                  </span>
                  <span className="text-slate-600 dark:text-slate-400">
                    {thesis.industryProfile.trends}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                    Competition:{" "}
                  </span>
                  <span className="text-slate-600 dark:text-slate-400">
                    {thesis.industryProfile.competition}
                  </span>
                </div>
              </div>
            </div>

            {/* Porter's 5 Forces */}
            <div>
              <h3 className="text-lg font-semibold mb-4">
                Porter&apos;s 5 Forces Analysis
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ForceCard
                  title="Threat of New Entrants"
                  content={thesis.porter.threatOfEntrants}
                />
                <ForceCard
                  title="Supplier Power"
                  content={thesis.porter.bargainingPowerSuppliers}
                />
                <ForceCard
                  title="Buyer Power"
                  content={thesis.porter.bargainingPowerBuyers}
                />
                <ForceCard
                  title="Threat of Substitutes"
                  content={thesis.porter.threatOfSubstitutes}
                />
                <ForceCard
                  title="Competitive Rivalry"
                  content={thesis.porter.competitiveRivalry}
                  className="md:col-span-2"
                />
              </div>
            </div>
          </TabsContent>

          {/* 4. Drivers (SWOT-ish) */}
          <TabsContent value="drivers" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <DriverCard
                title="External Tailwinds"
                icon={<TrendingUp className="h-5 w-5 text-emerald-500" />}
                content={thesis.drivers.externalTailwinds}
                type="positive"
              />
              <DriverCard
                title="External Headwinds"
                icon={<TrendingDown className="h-5 w-5 text-red-500" />}
                content={thesis.drivers.externalHeadwinds}
                type="negative"
              />
              <DriverCard
                title="Internal Catalysts"
                icon={<Zap className="h-5 w-5 text-amber-500" />}
                content={thesis.drivers.internalCatalysts}
                type="positive"
              />
              <DriverCard
                title="Internal Drags"
                icon={<AlertTriangle className="h-5 w-5 text-orange-500" />}
                content={thesis.drivers.internalDrags}
                type="negative"
              />
            </div>
          </TabsContent>

          {/* 5. Management */}
          <TabsContent value="management" className="space-y-6 mt-6">
            <div className="space-y-4">
              <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                <h3 className="text-lg font-semibold flex items-center gap-2 mb-2">
                  <Users className="h-5 w-5 text-slate-500" /> Leadership
                </h3>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                  {thesis.managementProfile.leadership}
                </p>
              </div>
              <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                <h3 className="text-lg font-semibold flex items-center gap-2 mb-2">
                  <Briefcase className="h-5 w-5 text-slate-500" /> Compensation
                  & Alignment
                </h3>
                <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                  {thesis.managementProfile.compensationAlignment}
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

// Sub-components for cleaner render
function ForceCard({
  title,
  content,
  className,
}: {
  title: string;
  content: string;
  className?: string;
}) {
  return (
    <div
      className={`p-4 rounded-md bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 ${className}`}
    >
      <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100 mb-1">
        {title}
      </h4>
      <p className="text-sm text-slate-600 dark:text-slate-400">{content}</p>
    </div>
  );
}

function DriverCard({
  title,
  icon,
  content,
  type,
}: {
  title: string;
  icon: React.ReactNode;
  content: string;
  type: "positive" | "negative";
}) {
  const borderColor =
    type === "positive"
      ? "border-emerald-100 dark:border-emerald-900/30"
      : "border-red-100 dark:border-red-900/30";
  const bgColor =
    type === "positive"
      ? "bg-emerald-50/50 dark:bg-emerald-900/10"
      : "bg-red-50/50 dark:bg-red-900/10";

  return (
    <div className={`p-5 rounded-lg border ${borderColor} ${bgColor}`}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h4 className="font-semibold text-slate-900 dark:text-slate-100">
          {title}
        </h4>
      </div>
      <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
        {content}
      </p>
    </div>
  );
}
