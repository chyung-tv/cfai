"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, TrendingUp } from "lucide-react";
import { useRouter } from "next/navigation";

export default function NotFound() {
  const router = useRouter();

  const handleAnalyze = () => {
    // TODO: Implement analysis trigger
    // This will call the backend API to start analysis
    console.log("Start analysis");
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-2xl mx-auto">
        <Card className="border-2 shadow-lg">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-yellow-100 dark:bg-yellow-950">
                <AlertCircle className="h-12 w-12 text-yellow-600 dark:text-yellow-400" />
              </div>
            </div>
            <CardTitle className="text-2xl">Stock Not Yet Analyzed</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-center text-slate-600 dark:text-slate-400">
              This stock hasn&rsquo;t been analyzed yet. Click the button below
              to start a comprehensive AI-powered analysis.
            </p>

            <div className="flex flex-col gap-3">
              <Button size="lg" className="w-full h-12" onClick={handleAnalyze}>
                <TrendingUp className="h-5 w-5 mr-2" />
                Analyze This Stock
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="w-full h-12"
                onClick={() => router.push("/")}
              >
                Back to Home
              </Button>
            </div>

            <div className="mt-6 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <span className="font-semibold">Note:</span> Analysis typically
                takes 30-60 seconds and includes qualitative assessment, DCF
                modeling, and AI-generated insights.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
