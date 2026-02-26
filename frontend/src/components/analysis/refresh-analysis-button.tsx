"use client";

import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { forceRefreshAnalysis } from "@/lib/actions/analysis";
import { toast } from "sonner";

interface RefreshAnalysisButtonProps {
  ticker: string;
}

export function RefreshAnalysisButton({ ticker }: RefreshAnalysisButtonProps) {
  const router = useRouter();

  const handleRefresh = async () => {
    try {
      // Trigger new analysis
      await forceRefreshAnalysis(ticker);
      // Navigate to same page to trigger re-render
      // This will cause getAnalysis to return null (new analysis not done yet)
      // Which will show the AnalysisLoading component
      router.push(`/analysis/${ticker}`);
      router.refresh();
    } catch (error) {
      // Check for NO_ACCESS error
      if (error instanceof Error) {
        try {
          const errorData = JSON.parse(error.message);
          if (errorData.code === "NO_ACCESS") {
            toast.error("Beta access required", {
              description: "Please contact beta@cfai.com to request access.",
            });
            return;
          }
        } catch {
          // Not a JSON error, continue with default error handling
        }
      }
      console.error("Failed to refresh analysis:", error);
      toast.error("Failed to refresh analysis", {
        description: "Please try again later.",
      });
    }
  };

  return (
    <Button variant="outline" size="sm" onClick={handleRefresh}>
      <RefreshCw className="h-4 w-4 mr-2" />
      Re-run Analysis
    </Button>
  );
}
