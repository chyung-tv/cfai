import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Target } from "lucide-react";

interface VerdictCardProps {
  verdict: string;
  explanation: string;
  className?: string;
}

export function VerdictCard({
  verdict,
  explanation,
  className,
}: VerdictCardProps) {
  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-blue-600" />
          <CardTitle>The Verdict</CardTitle>
        </div>
        <CardDescription>
          AI assessment of market pricing legitimacy
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
            Qualitative Badge:
          </span>
          <Badge className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-1 text-sm">
            {verdict}
          </Badge>
        </div>
        <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
          {explanation}
        </p>
      </CardContent>
    </Card>
  );
}
