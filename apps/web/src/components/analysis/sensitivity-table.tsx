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
import {
  SENSITIVITY_RANGES,
  ANALYSIS_CONSTANTS,
  FEASIBILITY_COLORS,
} from "@/lib/constants";

type SensitivityTableProps = {
  currentPrice: number;
  calculatePrice: (growth: number, discount: number) => number;
  discountRates?: readonly number[];
  growthRates?: readonly number[];
  priceThreshold?: number;
  className?: string;
};

export function SensitivityTable({
  currentPrice,
  calculatePrice,
  discountRates = SENSITIVITY_RANGES.discountRates,
  growthRates = SENSITIVITY_RANGES.growthRates,
  priceThreshold = 15,
  className,
}: SensitivityTableProps) {
  const getCellColor = (growth: number) => {
    const historicalAvg = ANALYSIS_CONSTANTS.HISTORICAL_AVG_GROWTH;
    const tolerance = ANALYSIS_CONSTANTS.GROWTH_TOLERANCE;

    if (growth < historicalAvg) return FEASIBILITY_COLORS.HIGH;
    if (growth <= historicalAvg + tolerance) return FEASIBILITY_COLORS.MEDIUM;
    return FEASIBILITY_COLORS.LOW;
  };

  const isCurrentPrice = (price: number) => {
    return Math.abs(price - currentPrice) < priceThreshold;
  };

  return (
    <Card className={`border-2 shadow-lg ${className || ""}`}>
      <CardHeader>
        <CardTitle>Sensitivity Table (Feasibility Heatmap)</CardTitle>
        <CardDescription>
          Share price scenarios based on growth rate and discount rate
          assumptions
        </CardDescription>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <div className="mb-4 flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-100 dark:bg-green-950 border border-green-300 dark:border-green-800" />
            <span className="text-slate-600 dark:text-slate-400">
              High Probability (Below Historical Avg)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-yellow-100 dark:bg-yellow-950 border border-yellow-300 dark:border-yellow-800" />
            <span className="text-slate-600 dark:text-slate-400">
              Medium Probability (Near Historical Avg)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-100 dark:bg-red-950 border border-red-300 dark:border-red-800" />
            <span className="text-slate-600 dark:text-slate-400">
              Low Probability (Above Historical Avg)
            </span>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="font-bold">Growth % / Discount %</TableHead>
              {discountRates.map((rate) => (
                <TableHead key={rate} className="text-center font-bold">
                  {rate}%
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {growthRates.map((growth) => (
              <TableRow key={growth}>
                <TableCell className="font-medium">{growth}%</TableCell>
                {discountRates.map((discount) => {
                  const price = calculatePrice(growth, discount);
                  const isMarketPrice = isCurrentPrice(price);
                  return (
                    <TableCell
                      key={`${growth}-${discount}`}
                      className={`text-center font-semibold ${getCellColor(growth)} ${
                        isMarketPrice
                          ? "ring-2 ring-blue-600 dark:ring-blue-400 ring-offset-2"
                          : ""
                      }`}
                    >
                      ${price}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <p className="text-sm text-slate-600 dark:text-slate-400 mt-4">
          <span className="font-semibold">Note:</span> Cells with a blue ring
          indicate scenarios close to the current market price of $
          {currentPrice}. Historical average growth:{" "}
          {ANALYSIS_CONSTANTS.HISTORICAL_AVG_GROWTH}
          %.
        </p>
      </CardContent>
    </Card>
  );
}
