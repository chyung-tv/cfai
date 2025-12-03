import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

interface GapAnalysisCardProps {
  marketExpects: number | string;
  aiPredicts: string;
  rationale: string;
  className?: string;
}

export function GapAnalysisCard({
  marketExpects,
  aiPredicts,
  rationale,
  className,
}: GapAnalysisCardProps) {
  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <CardTitle>The &ldquo;Gap&rdquo; Analysis</CardTitle>
        </div>
        <CardDescription>Market expectations vs AI predictions</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
            <div className="text-sm text-blue-600 dark:text-blue-400 font-medium mb-1">
              Market Expects
            </div>
            <div className="text-3xl font-bold text-blue-900 dark:text-blue-100">
              {typeof marketExpects === "number"
                ? `${marketExpects}% Growth`
                : marketExpects}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800">
            <div className="text-sm text-indigo-600 dark:text-indigo-400 font-medium mb-1">
              AI Predicts
            </div>
            <div className="text-3xl font-bold text-indigo-900 dark:text-indigo-100">
              {aiPredicts}
            </div>
          </div>
        </div>
        <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border">
          <div className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
            Rationale
          </div>
          <p className="text-slate-600 dark:text-slate-400">{rationale}</p>
        </div>
      </CardContent>
    </Card>
  );
}
