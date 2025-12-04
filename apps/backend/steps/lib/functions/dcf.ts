/**
 * DCF Valuation Model
 *
 * This module implements a Discounted Cash Flow (DCF) valuation model that:
 * - Uses provided TTM financial data
 * - Projects future cash flows based on AI-provided growth assumptions
 * - Calculates intrinsic value per share using the Gordon Growth Model
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Input parameters for DCF valuation
 */
export type DCFInputs = {
  symbol: string;
  aiParams: {
    revenueGrowthRates: number[]; // e.g., [0.15, 0.12, 0.10, 0.08, 0.06]
    terminalGrowthRate: number; // e.g., 0.03 for 3%
    discountRate: number; // e.g., 0.10 for 10%
  };
  financials: {
    revenueTTM: number;
    fcfTTM: number;
    sharesOutstanding: number;
    netDebt: number;
  };
};

/**
 * Single year projection in the DCF model
 */
export type DCFProjectionStep = {
  year: number;
  revenue: number;
  fcf: number;
  pvFCF: number; // Present value of FCF
};

// ============================================================================
// MAIN FUNCTION
// ============================================================================

/**
 * Performs a custom DCF valuation
 *
 * Steps:
 * 1. Fetches TTM financial data from API
 * 2. Calculates implied FCF margin from historical data
 * 3. Projects future cash flows using AI growth rates
 * 4. Discounts cash flows to present value
 * 5. Calculates terminal value using Gordon Growth Model
 * 6. Derives intrinsic value per share
 */
export async function performCustomDCF(inputs: DCFInputs) {
  console.log("\n=== Performing custom DCF valuation ===");
  console.log("Symbol:", inputs.symbol);
  console.log("AI Params:", inputs.aiParams);
  const { symbol, aiParams, financials } = inputs;

  // --------------------------------------------------------------------------
  // Step 1: Use Provided Financial Data
  // --------------------------------------------------------------------------

  console.log("\n[Step 1] Using provided financial data for", symbol, "...");

  const { revenueTTM, fcfTTM, sharesOutstanding, netDebt } = financials;

  console.log("\nMetrics:");
  console.log("  Revenue (TTM):", revenueTTM?.toLocaleString());
  console.log("  FCF (TTM):", fcfTTM?.toLocaleString());
  console.log("  Shares Outstanding:", sharesOutstanding?.toLocaleString());
  console.log("  Net Debt:", netDebt?.toLocaleString());

  // Validate data sanity
  if (revenueTTM <= 0 || sharesOutstanding <= 0) {
    console.error("❌ Invalid metrics: revenue and shares must be positive");
    return null;
  }

  // --------------------------------------------------------------------------
  // Step 2: Calculate Baseline Metrics
  // --------------------------------------------------------------------------

  console.log("\n[Step 2] Calculating baseline metrics...");
  // FCF Margin = FCF / Revenue (assumes this ratio holds in future)
  const impliedMargin = fcfTTM / revenueTTM;
  const usedDiscountRate = aiParams.discountRate;
  console.log("  Implied FCF Margin:", (impliedMargin * 100).toFixed(2) + "%");
  console.log("  Discount Rate:", (usedDiscountRate * 100).toFixed(2) + "%");

  // --------------------------------------------------------------------------
  // Step 3: Project Future Cash Flows
  // --------------------------------------------------------------------------

  console.log("\n[Step 3] Projecting future cash flows...");
  let currentRevenue = revenueTTM;
  let sumPvFcf = 0;
  const projections: DCFProjectionStep[] = [];

  aiParams.revenueGrowthRates.forEach((growthRate, index) => {
    const year = index + 1;

    // Grow revenue
    currentRevenue = currentRevenue * (1 + growthRate);

    // Derive FCF from revenue using implied margin
    const projectedFcf = currentRevenue * impliedMargin;

    // Discount to present value: FCF / (1 + r)^n
    const discountFactor = Math.pow(1 + usedDiscountRate, year);
    const pvFcf = projectedFcf / discountFactor;

    sumPvFcf += pvFcf;

    projections.push({
      year,
      revenue: currentRevenue,
      fcf: projectedFcf,
      pvFCF: pvFcf,
    });

    console.log(
      `  Year ${year}: Revenue=${currentRevenue.toLocaleString()}, FCF=${projectedFcf.toLocaleString()}, PV=${pvFcf.toLocaleString()}`
    );
  });
  console.log("  Sum of PV FCFs:", sumPvFcf.toLocaleString());

  // --------------------------------------------------------------------------
  // Step 4: Calculate Terminal Value
  // --------------------------------------------------------------------------

  console.log("\n[Step 4] Calculating terminal value...");
  const finalProjectedFcf = projections[projections.length - 1].fcf;

  // Gordon Growth Model: TV = FCF(n+1) / (r - g)
  const terminalValue =
    (finalProjectedFcf * (1 + aiParams.terminalGrowthRate)) /
    (usedDiscountRate - aiParams.terminalGrowthRate);

  // Discount terminal value to present
  const terminalDiscountFactor = Math.pow(
    1 + usedDiscountRate,
    projections.length
  );
  const presentTerminalValue = terminalValue / terminalDiscountFactor;

  console.log("  Terminal Value:", terminalValue.toLocaleString());
  console.log(
    "  Present Terminal Value:",
    presentTerminalValue.toLocaleString()
  );

  // --------------------------------------------------------------------------
  // Step 5: Calculate Intrinsic Value
  // --------------------------------------------------------------------------

  console.log("\n[Step 5] Calculating intrinsic value...");
  // Enterprise Value = PV of projected FCFs + PV of terminal value
  const enterpriseValue = sumPvFcf + presentTerminalValue;
  console.log("  Enterprise Value:", enterpriseValue.toLocaleString());

  // Equity Value = Enterprise Value - Net Debt
  const equityValue = enterpriseValue - netDebt;
  console.log("  Equity Value:", equityValue.toLocaleString());

  // Intrinsic Value per Share = Equity Value / Shares Outstanding
  const intrinsicValuePerShare = equityValue / sharesOutstanding;
  console.log(
    "  Intrinsic Value per Share: $" + intrinsicValuePerShare.toFixed(2)
  );

  // --------------------------------------------------------------------------
  // Return Results
  // --------------------------------------------------------------------------

  const result = {
    intrinsicValuePerShare: Number(intrinsicValuePerShare.toFixed(2)),
    impliedMargin,
    usedDiscountRate,
    sumPvFcf,
    terminalValue,
    presentTerminalValue,
    enterpriseValue,
    equityValue,
    projections,
    upsideDownside: 0, // Calculate in frontend vs live price
  };

  console.log("\n✅ DCF Calculation Complete!");
  console.log("===========================\n");
  return result;
}

// Infer the result type from the function's return type
export type DCFResult = Awaited<ReturnType<typeof performCustomDCF>>;
