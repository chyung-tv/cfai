"use client";

import { useEffect, useState } from "react";
import type { PackedAnalysisData } from "@repo/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Eye,
  CheckCircle2,
  XCircle,
  Loader2,
  TrendingDown,
  TrendingUp,
  Minus,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import {
  LEGITIMACY_THRESHOLDS,
  LEGITIMACY_COLORS,
  type LegitimacyLevel,
} from "@/lib/constants";
import {
  getUserQueryHistory,
  syncQueryStatus,
  markQueryAsFailed,
} from "@/lib/actions/dashboard";
import { triggerAnalysis } from "@/lib/actions/analysis";
import { useStreamGroup } from "@motiadev/stream-client-react";

type AnalysisStatus = "completed" | "processing" | "failed";

interface QueryWithResult {
  id: string;
  symbol: string;
  status: string;
  traceId: string | null;
  createdAt: Date;
  analysisResult: {
    id: string;
    price: number;
    dcf: PackedAnalysisData["dcf"];
  } | null;
}

function StatusBadge({ status }: { status: AnalysisStatus }) {
  const variants = {
    completed: {
      icon: CheckCircle2,
      className: "bg-green-500 hover:bg-green-600 text-white",
      label: "Completed",
    },
    processing: {
      icon: Loader2,
      className: "bg-blue-500 hover:bg-blue-600 text-white",
      label: "Processing",
    },
    failed: {
      icon: XCircle,
      className: "bg-red-500 hover:bg-red-600 text-white",
      label: "Failed",
    },
  };

  const variant = variants[status];
  const Icon = variant.icon;

  return (
    <Badge className={variant.className}>
      <Icon
        className={`h-3 w-3 mr-1 ${status === "processing" ? "animate-spin" : ""}`}
      />
      {variant.label}
    </Badge>
  );
}

function PriceLegitimacyBadge({
  analysisResult,
}: {
  analysisResult: QueryWithResult["analysisResult"];
}) {
  if (!analysisResult?.dcf) {
    return <span className="text-slate-400">—</span>;
  }

  const dcf = analysisResult.dcf;
  const impliedGrowth = dcf.scenarios?.[0]?.impliedGrowth;
  const aiPredictedGrowth = dcf.independentPrediction?.predictedCagr;

  if (
    impliedGrowth === null ||
    impliedGrowth === undefined ||
    aiPredictedGrowth === null ||
    aiPredictedGrowth === undefined
  ) {
    return <span className="text-slate-400">—</span>;
  }

  const gap = impliedGrowth - aiPredictedGrowth;
  let level: LegitimacyLevel;
  let icon;
  let label;

  if (gap < LEGITIMACY_THRESHOLDS.UNDERVALUED) {
    level = "UNDERVALUED";
    icon = TrendingDown;
    label = "Undervalued";
  } else if (gap > LEGITIMACY_THRESHOLDS.OVERVALUED) {
    level = "OVERVALUED";
    icon = TrendingUp;
    label = "Overvalued";
  } else {
    level = "FAIR";
    icon = Minus;
    label = "Fair";
  }

  const Icon = icon;

  return (
    <Badge className={LEGITIMACY_COLORS[level]}>
      <Icon className="h-3 w-3 mr-1" />
      {label}
    </Badge>
  );
}

function StatCard({
  title,
  value,
  className,
}: {
  title: string;
  value: number | string;
  className?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardDescription>{title}</CardDescription>
        <CardTitle className={`text-3xl ${className || ""}`}>{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function formatDate(date: Date) {
  const now = new Date();
  const diffMs = now.getTime() - new Date(date).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
  } else if (diffDays === 1) {
    return "Yesterday";
  } else {
    return new Date(date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
}

export default function DashboardPage() {
  const [queries, setQueries] = useState<QueryWithResult[]>([]);
  const [loading, setLoading] = useState(true);

  // Subscribe to stream events
  const { data: streamData = [] } = useStreamGroup<{
    id: string;
    symbol: string;
    status: string;
  }>({
    streamName: "stock-analysis-stream",
    groupId: "analysis",
  });

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getUserQueryHistory();
        setQueries(data as QueryWithResult[]);

        // Sync processing queries
        const processingQueries = data.filter((q) => q.status === "processing");
        for (const query of processingQueries) {
          await syncQueryStatus(query.id);
        }

        // Refresh data after sync
        if (processingQueries.length > 0) {
          const refreshedData = await getUserQueryHistory();
          setQueries(refreshedData as QueryWithResult[]);
        }
      } catch (error) {
        console.error("Failed to fetch queries:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Update status based on stream events
  useEffect(() => {
    if (streamData.length === 0 || queries.length === 0) return;

    // Use a flag to track if we need to refresh
    let needsRefresh = false;

    const updateQueries = async () => {
      for (const query of queries) {
        if (!query.traceId) continue;

        const event = streamData.find((item) => item.id === query.traceId);
        if (!event) continue;

        // Check if stream indicates completion
        if (event.status === "Analysis completed") {
          await syncQueryStatus(query.id);
          needsRefresh = true;
        }

        // Check if stream indicates failure
        if (
          event.status.toLowerCase().includes("error") ||
          event.status.toLowerCase().includes("failed")
        ) {
          await markQueryAsFailed(query.id);
          needsRefresh = true;
        }
      }

      // Refresh data if any status changed
      if (needsRefresh) {
        const refreshedData = await getUserQueryHistory();
        setQueries(refreshedData as QueryWithResult[]);
      }
    };

    updateQueries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamData]);

  const handleRetry = async (symbol: string) => {
    try {
      await triggerAnalysis(symbol);
      // Refresh the list
      const data = await getUserQueryHistory();
      setQueries(data as QueryWithResult[]);
    } catch (error) {
      console.error("Failed to retry analysis:", error);
    }
  };

  if (loading) {
    return (
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="container mx-auto px-4 py-16">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Dashboard
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            View and manage your stock analysis history
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-4 gap-4">
          <StatCard title="Total Analyses" value={queries.length} />
          <StatCard
            title="Completed"
            value={queries.filter((q) => q.status === "completed").length}
            className="text-green-600"
          />
          <StatCard
            title="Processing"
            value={queries.filter((q) => q.status === "processing").length}
            className="text-blue-600"
          />
          <StatCard
            title="Failed"
            value={queries.filter((q) => q.status === "failed").length}
            className="text-red-600"
          />
        </div>

        {/* Analysis History Table */}
        <Card>
          <CardHeader>
            <CardTitle>Analysis History</CardTitle>
            <CardDescription>
              Recent stock analyses and their current status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {queries.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  No analyses yet. Start by searching for a stock symbol above.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Requested</TableHead>
                    <TableHead>Price Legitimacy</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {queries.map((query) => (
                    <TableRow key={query.id}>
                      <TableCell className="font-semibold">
                        {query.symbol}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={query.status as AnalysisStatus} />
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {formatDate(query.createdAt)}
                      </TableCell>
                      <TableCell>
                        <PriceLegitimacyBadge
                          analysisResult={query.analysisResult}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        {query.status === "completed" ? (
                          <Link href={`/analysis/${query.symbol}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4 mr-2" />
                              View
                            </Button>
                          </Link>
                        ) : query.status === "processing" ? (
                          <Button variant="ghost" size="sm" disabled>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRetry(query.symbol)}
                          >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Retry
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
