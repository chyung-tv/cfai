// Analysis constants
export const ANALYSIS_CONSTANTS = {
  CACHE_DAYS: 7,
  HISTORICAL_AVG_GROWTH: 15,
  GROWTH_TOLERANCE: 5,
} as const;

// UI constants for sensitivity table
export const SENSITIVITY_RANGES = {
  discountRates: [8, 9, 10, 11, 12],
  growthRates: [10, 12.5, 15, 17.5, 20, 22.5, 25],
} as const;

// Color classification thresholds
export const FEASIBILITY_COLORS = {
  HIGH: "bg-green-100 dark:bg-green-950 text-green-800 dark:text-green-200",
  MEDIUM:
    "bg-yellow-100 dark:bg-yellow-950 text-yellow-800 dark:text-yellow-200",
  LOW: "bg-red-100 dark:bg-red-950 text-red-800 dark:text-red-200",
} as const;

// Badge variants for qualitative ratings
export const VERDICT_VARIANTS = {
  VERY_LIKELY: "bg-green-500 hover:bg-green-600",
  LIKELY: "bg-lime-500 hover:bg-lime-600",
  POSSIBLE: "bg-yellow-500 hover:bg-yellow-600",
  UNLIKELY: "bg-orange-500 hover:bg-orange-600",
  VERY_UNLIKELY: "bg-red-500 hover:bg-red-600",
} as const;

export type VerdictType = keyof typeof VERDICT_VARIANTS;

// Price legitimacy thresholds (based on CAGR gap)
export const LEGITIMACY_THRESHOLDS = {
  UNDERVALUED: -10, // Implied growth < Analyzed growth - 10%
  OVERVALUED: 10, // Implied growth > Analyzed growth + 10%
} as const;

export const LEGITIMACY_COLORS = {
  UNDERVALUED: "bg-green-500 hover:bg-green-600 text-white", // Market expects less than AI predicts
  FAIR: "bg-yellow-500 hover:bg-yellow-600 text-white", // Within ±10% range
  OVERVALUED: "bg-red-500 hover:bg-red-600 text-white", // Market expects more than AI predicts
} as const;

export type LegitimacyLevel = keyof typeof LEGITIMACY_COLORS;
