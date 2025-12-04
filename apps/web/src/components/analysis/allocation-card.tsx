import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wallet, Briefcase, AlertTriangle, PieChart } from "lucide-react";

interface AllocationCardProps {
  recommendation: string;
  portfolioRole: string;
  riskProfile: string;
  allocation: number;
  reasoning: string;
  className?: string;
}

export function AllocationCard({
  recommendation,
  portfolioRole,
  riskProfile,
  allocation,
  reasoning,
  className,
}: AllocationCardProps) {
  // Helper to format snake_case to Title Case
  const formatText = (text: string) =>
    text
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");

  // Helper for recommendation color
  const getRecColor = (rec: string) => {
    if (rec.includes("buy") || rec.includes("accumulate"))
      return "bg-emerald-600 hover:bg-emerald-700";
    if (rec.includes("hold")) return "bg-blue-600 hover:bg-blue-700";
    if (rec.includes("sell") || rec.includes("reduce"))
      return "bg-red-600 hover:bg-red-700";
    return "bg-slate-600 hover:bg-slate-700";
  };

  // Helper for risk color
  const getRiskColor = (risk: string) => {
    if (risk.includes("low"))
      return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (risk.includes("moderate"))
      return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Wallet className="h-5 w-5 text-purple-600" />
          <CardTitle>Investment Thesis & Allocation</CardTitle>
        </div>
        <CardDescription>
          Strategic portfolio fit and actionable advice
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Top Row: The Big Decision */}
        <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-4">
            <Badge
              className={`${getRecColor(recommendation)} text-white text-lg px-6 py-2 shadow-sm`}
            >
              {formatText(recommendation)}
            </Badge>
            <div className="flex flex-col">
              <span className="text-xs text-slate-500 font-medium uppercase">
                Target Allocation
              </span>
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {allocation}%
              </span>
            </div>
          </div>

          {/* Divider for mobile */}
          <div className="w-full h-px bg-slate-200 dark:bg-slate-700 md:hidden" />

          {/* Secondary Metrics */}
          <div className="flex gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border bg-white dark:bg-slate-950">
              <Briefcase className="w-4 h-4 text-slate-500" />
              <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 uppercase font-bold">
                  Role
                </span>
                <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  {formatText(portfolioRole)}
                </span>
              </div>
            </div>

            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${getRiskColor(riskProfile)}`}
            >
              <AlertTriangle className="w-4 h-4" />
              <div className="flex flex-col">
                <span className="text-[10px] opacity-70 uppercase font-bold">
                  Risk
                </span>
                <span className="text-xs font-medium">
                  {formatText(riskProfile)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Reasoning */}
        <div>
          <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
            <PieChart className="w-4 h-4 text-slate-500" />
            Thesis Rationale
          </h4>
          <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
            {reasoning}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
