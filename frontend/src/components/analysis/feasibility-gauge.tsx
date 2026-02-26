import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";
import type { GrowthJudgement } from "@repo/types";

// Re-export types for convenience
type FeasibilityLevel = GrowthJudgement["scenarios"][number]["feasibility"];
type Scenario = GrowthJudgement["scenarios"][number];

interface FeasibilityGaugeProps {
  scenarios: Scenario[];
  independentPrediction: number;
  currentPrice: number;
  className?: string;
}

const FEASIBILITY_CONFIG: Record<
  FeasibilityLevel,
  { label: string; color: string; bg: string; border: string }
> = {
  VERY_HIGH: {
    label: "Very High",
    color: "text-green-700 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-950/30",
    border: "border-green-200 dark:border-green-800",
  },
  HIGH: {
    label: "High",
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-emerald-200 dark:border-emerald-800",
  },
  MEDIUM: {
    label: "Medium",
    color: "text-yellow-600 dark:text-yellow-400",
    bg: "bg-yellow-50 dark:bg-yellow-950/30",
    border: "border-yellow-200 dark:border-yellow-800",
  },
  LOW: {
    label: "Low",
    color: "text-orange-600 dark:text-orange-400",
    bg: "bg-orange-50 dark:bg-orange-950/30",
    border: "border-orange-200 dark:border-orange-800",
  },
  VERY_LOW: {
    label: "Very Low",
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-200 dark:border-red-800",
  },
};

export function FeasibilityGauge({
  scenarios,
  independentPrediction,
  currentPrice,
  className,
}: FeasibilityGaugeProps) {
  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Growth Feasibility Gauge
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-slate-400" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p>
                      Compares the market&apos;s required growth rate (to
                      achieve your target return) against our AI&apos;s
                      independent growth prediction.
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </CardTitle>
            <CardDescription>
              Can the company grow fast enough to give you these returns?
            </CardDescription>
          </div>
          <div className="flex gap-8 text-right">
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">
                Current Price
              </div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                ${currentPrice}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">
                AI Predicted Growth
              </div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {(independentPrediction * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[140px]">Target Return</TableHead>
              <TableHead className="w-[140px]">Required Growth</TableHead>
              <TableHead className="w-[140px]">Feasibility</TableHead>
              <TableHead>AI Analysis</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {scenarios.map((scenario) => {
              const config = FEASIBILITY_CONFIG[scenario.feasibility];
              return (
                <TableRow key={scenario.discountRate}>
                  <TableCell className="font-medium">
                    {(scenario.discountRate * 100).toFixed(1)}%
                  </TableCell>
                  <TableCell>
                    {(scenario.impliedGrowth * 100).toFixed(1)}%
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={`${config.bg} ${config.color} ${config.border} font-semibold`}
                    >
                      {config.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-slate-600 dark:text-slate-300">
                    {scenario.gapAnalysis}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
