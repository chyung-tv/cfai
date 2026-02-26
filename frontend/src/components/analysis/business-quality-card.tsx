import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, ShieldCheck, TrendingUp, Users } from "lucide-react";
import { formatSnakeCase } from "@/lib/utils";

interface BusinessQualityCardProps {
  tier: string;
  moat: string;
  marketStructure: string;
  explanation: string;
  className?: string;
}

export function BusinessQualityCard({
  tier,
  moat,
  marketStructure,
  explanation,
  className,
}: BusinessQualityCardProps) {

  // Helper for tier color
  const getTierColor = (tier: string) => {
    if (tier.includes("enduring") || tier.includes("strong"))
      return "bg-emerald-500 hover:bg-emerald-600";
    if (tier.includes("good")) return "bg-blue-500 hover:bg-blue-600";
    if (tier.includes("nothing")) return "bg-yellow-500 hover:bg-yellow-600";
    return "bg-red-500 hover:bg-red-600";
  };

  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-emerald-600" />
          <CardTitle>Business Quality</CardTitle>
        </div>
        <CardDescription>
          Fundamental strength and competitive advantage
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Key Metrics Row */}
        <div className="flex flex-wrap gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Quality Tier
            </span>
            <Badge
              className={`${getTierColor(tier)} text-white px-3 py-1 text-sm w-fit`}
            >
              <ShieldCheck className="w-3 h-3 mr-1" />
              {formatSnakeCase(tier)}
            </Badge>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Primary Moat
            </span>
            <Badge variant="outline" className="px-3 py-1 text-sm w-fit">
              <TrendingUp className="w-3 h-3 mr-1 text-slate-500" />
              {formatSnakeCase(moat)}
            </Badge>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Market Structure
            </span>
            <Badge variant="secondary" className="px-3 py-1 text-sm w-fit">
              <Users className="w-3 h-3 mr-1 text-slate-500" />
              {formatSnakeCase(marketStructure)}
            </Badge>
          </div>
        </div>

        {/* Explanation */}
        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-lg border border-slate-100 dark:border-slate-800">
          <p className="text-slate-700 dark:text-slate-300 leading-relaxed text-sm">
            {explanation}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
