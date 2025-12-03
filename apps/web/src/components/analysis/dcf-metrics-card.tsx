import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Calculator } from "lucide-react";

interface DCFMetricsCardProps {
  currentPrice: number;
  impliedGrowth: number;
  discountRate: number;
  isDiscountRateEditable?: boolean;
  className?: string;
}

export function DCFMetricsCard({
  currentPrice,
  impliedGrowth,
  discountRate,
  isDiscountRateEditable = false,
  className,
}: DCFMetricsCardProps) {
  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Calculator className="h-5 w-5 text-blue-600" />
          <CardTitle>The Math (Reverse DCF)</CardTitle>
        </div>
        <CardDescription>
          Key metrics derived from current pricing
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-linear-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 border">
            <div className="text-sm text-slate-600 dark:text-slate-400 mb-1">
              Current Price
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              ${currentPrice}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-linear-to-br from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border border-blue-200 dark:border-blue-800">
            <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
              Implied Growth Required
            </div>
            <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
              {impliedGrowth}%
            </div>
          </div>
          <div className="p-4 rounded-lg bg-linear-to-br from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950 border border-purple-200 dark:border-purple-800">
            <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
              Discount Rate Used
            </div>
            <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
              {discountRate}%
              {isDiscountRateEditable && (
                <span className="text-sm font-normal text-purple-600 dark:text-purple-400 ml-1">
                  (Editable)
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
