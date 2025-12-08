import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header Skeleton */}
        <div className="text-center space-y-4">
          <div className="h-12 bg-slate-200 dark:bg-slate-800 rounded-lg w-64 mx-auto animate-pulse" />
          <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded-lg w-96 mx-auto animate-pulse" />
        </div>

        {/* Analysis Status */}
        <Card className="border-2 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-center gap-3">
              <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
              <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Analyzing Stock...
              </h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
                <p className="text-slate-600 dark:text-slate-400">
                  Processing qualitative analysis...
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-700" />
                <p className="text-slate-400 dark:text-slate-600">
                  Evaluating financial projections...
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-700" />
                <p className="text-slate-400 dark:text-slate-600">
                  Calculating DCF model...
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-700" />
                <p className="text-slate-400 dark:text-slate-600">
                  Generating final rating...
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Skeletons */}
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="border-2 shadow-lg">
              <CardHeader>
                <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-48 animate-pulse" />
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-64 animate-pulse mt-2" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full animate-pulse" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-5/6 animate-pulse" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-4/6 animate-pulse" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
