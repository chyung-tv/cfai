"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App route error:", error);
  }, [error]);

  return (
    <section className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto space-y-6 text-center">
        <AlertCircle className="mx-auto h-16 w-16 text-red-500" />
        <div className="space-y-2">
          <h2 className="text-2xl font-bold">Error Loading Page</h2>
          <p className="text-muted-foreground">
            We couldn't load this page. Please try again.
          </p>
        </div>
        <div className="flex gap-3 justify-center">
          <Button onClick={reset}>Retry</Button>
          <Button
            variant="outline"
            onClick={() => (window.location.href = "/dashboard")}
          >
            Go to Dashboard
          </Button>
        </div>
      </div>
    </section>
  );
}
