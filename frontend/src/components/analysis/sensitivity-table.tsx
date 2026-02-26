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

type SensitivityTableProps = {
  currentPrice: number;
  sensitivity: {
    terminalGrowthRates: number[];
    discountRates: number[];
    values: number[][];
  };
  usedDiscountRate: number;
  className?: string;
};

export function SensitivityTable({
  currentPrice,
  sensitivity,
  usedDiscountRate,
  className,
}: SensitivityTableProps) {
  // Find base case indices (closest to the used discount rate)
  const baseDiscountIndex = sensitivity.discountRates.findIndex(
    (rate) => Math.abs(rate - usedDiscountRate) < 0.0001
  );
  const baseGrowthIndex = Math.floor(
    sensitivity.terminalGrowthRates.length / 2
  );

  // Helper to calculate upside/downside percentage
  const getUpsideDownside = (intrinsicValue: number): number => {
    return ((intrinsicValue - currentPrice) / currentPrice) * 100;
  };

  // 7-tier gradient: Deep Green -> Light Green -> Yellow -> Light Red -> Deep Red
  const getGradientColor = (upsideDownside: number): string => {
    if (upsideDownside >= 30)
      return "bg-green-600 dark:bg-green-700 text-white";
    if (upsideDownside >= 20)
      return "bg-green-400 dark:bg-green-600 text-white";
    if (upsideDownside >= 10)
      return "bg-green-200 dark:bg-green-800 text-slate-900 dark:text-slate-100";
    if (upsideDownside >= -10)
      return "bg-yellow-200 dark:bg-yellow-800 text-slate-900 dark:text-slate-100";
    if (upsideDownside >= -20)
      return "bg-red-200 dark:bg-red-800 text-slate-900 dark:text-slate-100";
    if (upsideDownside >= -30) return "bg-red-400 dark:bg-red-600 text-white";
    return "bg-red-600 dark:bg-red-700 text-white";
  };

  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <CardTitle>Valuation Sensitivity Matrix</CardTitle>
        <CardDescription>
          Intrinsic value scenarios across discount rates and terminal growth
          assumptions
        </CardDescription>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        {/* Legend */}
        <div className="mb-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg space-y-2">
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Reading the Matrix:
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            • Each cell shows:{" "}
            <span className="font-mono">
              Intrinsic Value (Upside/Downside %)
            </span>
          </p>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            • Current Price:{" "}
            <span className="font-semibold">${currentPrice.toFixed(2)}</span>
          </p>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-600 dark:text-slate-400">
              Color Scale:
            </span>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-600 dark:bg-green-700 rounded" />
              <span className="text-slate-500 dark:text-slate-500">+30%</span>
              <div className="w-3 h-3 bg-green-400 dark:bg-green-600 rounded" />
              <span className="text-slate-500 dark:text-slate-500">+20%</span>
              <div className="w-3 h-3 bg-green-200 dark:bg-green-800 rounded" />
              <span className="text-slate-500 dark:text-slate-500">+10%</span>
              <div className="w-3 h-3 bg-yellow-200 dark:bg-yellow-800 rounded" />
              <span className="text-slate-500 dark:text-slate-500">±10%</span>
              <div className="w-3 h-3 bg-red-200 dark:bg-red-800 rounded" />
              <span className="text-slate-500 dark:text-slate-500">-20%</span>
              <div className="w-3 h-3 bg-red-400 dark:bg-red-600 rounded" />
              <span className="text-slate-500 dark:text-slate-500">-30%</span>
              <div className="w-3 h-3 bg-red-600 dark:bg-red-700 rounded" />
            </div>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="font-bold">
                Discount Rate \ Terminal Growth
              </TableHead>
              {sensitivity.terminalGrowthRates.map((rate, idx) => (
                <TableHead
                  key={idx}
                  className="text-center font-bold min-w-[140px]"
                >
                  {(rate * 100).toFixed(2)}%
                  {idx === baseGrowthIndex && (
                    <div className="text-xs font-normal text-slate-500 dark:text-slate-400">
                      (base)
                    </div>
                  )}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sensitivity.discountRates.map((discountRate, dIdx) => (
              <TableRow key={dIdx}>
                <TableCell className="font-medium">
                  {(discountRate * 100).toFixed(2)}%
                  {dIdx === baseDiscountIndex && (
                    <span className="text-xs text-slate-500 dark:text-slate-400 ml-2">
                      (base)
                    </span>
                  )}
                </TableCell>
                {sensitivity.terminalGrowthRates.map((_, gIdx) => {
                  const intrinsicValue = sensitivity.values[dIdx][gIdx];
                  const upsideDownside = getUpsideDownside(intrinsicValue);
                  const cellColor = getGradientColor(upsideDownside);

                  return (
                    <TableCell
                      key={`${dIdx}-${gIdx}`}
                      className={`text-center text-xs font-semibold ${cellColor}`}
                    >
                      <div>${intrinsicValue.toFixed(2)}</div>
                      <div className="text-[10px] opacity-90">
                        ({upsideDownside >= 0 ? "+" : ""}
                        {upsideDownside.toFixed(1)}%)
                      </div>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <p className="text-sm text-slate-600 dark:text-slate-400 mt-4">
          <span className="font-semibold">Note:</span> Rows/columns marked
          &quot;(base)&quot; indicate the assumptions used in the primary DCF
          calculation.
        </p>
      </CardContent>
    </Card>
  );
}
