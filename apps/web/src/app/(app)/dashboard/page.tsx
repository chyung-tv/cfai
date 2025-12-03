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
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  TrendingDown,
  TrendingUp,
  Minus,
} from "lucide-react";
import Link from "next/link";
import {
  LEGITIMACY_THRESHOLDS,
  LEGITIMACY_COLORS,
  type LegitimacyLevel,
} from "@/lib/constants";

// Mock data - replace with actual API fetch
const mockAnalyses = [
  {
    id: "1",
    symbol: "AAPL",
    status: "completed",
    impliedGrowth: 18,
    aiPredictedGrowth: 14, // Gap: +4% → Fair (Yellow)
    createdAt: new Date("2025-12-03T10:30:00"),
  },
  {
    id: "2",
    symbol: "GOOGL",
    status: "processing",
    impliedGrowth: null,
    aiPredictedGrowth: null,
    createdAt: new Date("2025-12-03T11:15:00"),
  },
  {
    id: "3",
    symbol: "MSFT",
    status: "completed",
    impliedGrowth: 12,
    aiPredictedGrowth: 15, // Gap: -3% → Undervalued (Green)
    createdAt: new Date("2025-12-02T14:20:00"),
  },
  {
    id: "4",
    symbol: "TSLA",
    status: "failed",
    impliedGrowth: null,
    aiPredictedGrowth: null,
    createdAt: new Date("2025-12-02T09:45:00"),
  },
  {
    id: "5",
    symbol: "NVDA",
    status: "completed",
    impliedGrowth: 25,
    aiPredictedGrowth: 12, // Gap: +13% → Overvalued (Red)
    createdAt: new Date("2025-12-01T16:30:00"),
  },
];

type AnalysisStatus = "completed" | "processing" | "failed" | "pending";

interface Analysis {
  id: string;
  symbol: string;
  status: string;
  impliedGrowth: number | null;
  aiPredictedGrowth: number | null;
  createdAt: Date;
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
    pending: {
      icon: Clock,
      className: "bg-yellow-500 hover:bg-yellow-600 text-white",
      label: "Pending",
    },
  };

  const variant = variants[status];
  const Icon = variant.icon;

  return (
    <Badge className={variant.className}>
      <Icon className="h-3 w-3 mr-1" />
      {variant.label}
    </Badge>
  );
}

function PriceLegitimacyBadge({
  impliedGrowth,
  aiPredictedGrowth,
}: {
  impliedGrowth: number | null;
  aiPredictedGrowth: number | null;
}) {
  if (impliedGrowth === null || aiPredictedGrowth === null) {
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
  const diffMs = now.getTime() - date.getTime();
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
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
}

export default function DashboardPage() {
  // TODO: Fetch actual data from backend
  // const response = await fetch('http://localhost:3001/api/history');
  // const analyses = await response.json();

  const analyses = mockAnalyses;

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
          <StatCard title="Total Analyses" value={analyses.length} />
          <StatCard
            title="Completed"
            value={analyses.filter((a) => a.status === "completed").length}
            className="text-green-600"
          />
          <StatCard
            title="Processing"
            value={analyses.filter((a) => a.status === "processing").length}
            className="text-blue-600"
          />
          <StatCard
            title="Failed"
            value={analyses.filter((a) => a.status === "failed").length}
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
            {analyses.length === 0 ? (
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
                  {analyses.map((analysis) => (
                    <TableRow key={analysis.id}>
                      <TableCell className="font-semibold">
                        {analysis.symbol}
                      </TableCell>
                      <TableCell>
                        <StatusBadge
                          status={analysis.status as AnalysisStatus}
                        />
                      </TableCell>
                      <TableCell className="text-slate-600 dark:text-slate-400">
                        {formatDate(analysis.createdAt)}
                      </TableCell>
                      <TableCell>
                        <PriceLegitimacyBadge
                          impliedGrowth={analysis.impliedGrowth}
                          aiPredictedGrowth={analysis.aiPredictedGrowth}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        {analysis.status === "completed" ? (
                          <Link href={`/analysis/${analysis.symbol}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4 mr-2" />
                              View
                            </Button>
                          </Link>
                        ) : analysis.status === "processing" ? (
                          <Button variant="ghost" size="sm" disabled>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing
                          </Button>
                        ) : (
                          <Link href={`/analysis/${analysis.symbol}`}>
                            <Button variant="ghost" size="sm">
                              Retry
                            </Button>
                          </Link>
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
