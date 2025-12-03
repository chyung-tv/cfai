import { config } from "dotenv";
config({ path: ".env.local" });

import z from "zod";

export const balanceSheetDataSchema = z.array(
  z.object({
    date: z.string(), // Date of the report
    symbol: z.string(), // Stock symbol
    reportedCurrency: z.string(), // Currency used in the report
    cik: z.string(), // Central Index Key (CIK) identifier
    filingDate: z.string(), // Filing date of the report
    acceptedDate: z.string(), // Accepted date of the report
    fiscalYear: z.string(), // Fiscal year of the report
    period: z.string(), // Reporting period (e.g., FY, Q1, etc.)
    cashAndCashEquivalents: z.number(), // Cash and cash equivalents
    shortTermInvestments: z.number(), // Short-term investments
    cashAndShortTermInvestments: z.number(), // Total cash and short-term investments
    netReceivables: z.number(), // Net receivables
    accountsReceivables: z.number(), // Accounts receivables
    otherReceivables: z.number(), // Other receivables
    inventory: z.number(), // Inventory
    prepaids: z.number(), // Prepaid expenses
    otherCurrentAssets: z.number(), // Other current assets
    totalCurrentAssets: z.number(), // Total current assets
    propertyPlantEquipmentNet: z.number(), // Net property, plant, and equipment
    goodwill: z.number(), // Goodwill
    intangibleAssets: z.number(), // Intangible assets
    goodwillAndIntangibleAssets: z.number(), // Combined goodwill and intangible assets
    longTermInvestments: z.number(), // Long-term investments
    taxAssets: z.number(), // Tax assets
    otherNonCurrentAssets: z.number(), // Other non-current assets
    totalNonCurrentAssets: z.number(), // Total non-current assets
    otherAssets: z.number(), // Other assets
    totalAssets: z.number(), // Total assets
    totalPayables: z.number(), // Total payables
    accountPayables: z.number(), // Account payables
    otherPayables: z.number(), // Other payables
    accruedExpenses: z.number(), // Accrued expenses
    shortTermDebt: z.number(), // Short-term debt
    capitalLeaseObligationsCurrent: z.number(), // Current capital lease obligations
    taxPayables: z.number(), // Tax payables
    deferredRevenue: z.number(), // Deferred revenue
    otherCurrentLiabilities: z.number(), // Other current liabilities
    totalCurrentLiabilities: z.number(), // Total current liabilities
    longTermDebt: z.number(), // Long-term debt
    capitalLeaseObligationsNonCurrent: z.number(), // Non-current capital lease obligations
    deferredRevenueNonCurrent: z.number(), // Non-current deferred revenue
    deferredTaxLiabilitiesNonCurrent: z.number(), // Non-current deferred tax liabilities
    otherNonCurrentLiabilities: z.number(), // Other non-current liabilities
    totalNonCurrentLiabilities: z.number(), // Total non-current liabilities
    otherLiabilities: z.number(), // Other liabilities
    capitalLeaseObligations: z.number(), // Total capital lease obligations
    totalLiabilities: z.number(), // Total liabilities
    treasuryStock: z.number(), // Treasury stock
    preferredStock: z.number(), // Preferred stock
    commonStock: z.number(), // Common stock
    retainedEarnings: z.number(), // Retained earnings
    additionalPaidInCapital: z.number(), // Additional paid-in capital
    accumulatedOtherComprehensiveIncomeLoss: z.number(), // Accumulated other comprehensive income/loss
    otherTotalStockholdersEquity: z.number(), // Other total stockholders' equity
    totalStockholdersEquity: z.number(), // Total stockholders' equity
    totalEquity: z.number(), // Total equity
    minorityInterest: z.number(), // Minority interest
    totalLiabilitiesAndTotalEquity: z.number(), // Total liabilities and total equity
    totalInvestments: z.number(), // Total investments
    totalDebt: z.number(), // Total debt
    netDebt: z.number(), // Net debt
  })
);

export const incomeStatementDataSchema = z.array(
  z.object({
    date: z.string(), // Date of the report
    symbol: z.string(), // Stock symbol
    reportedCurrency: z.string(), // Currency used in the report
    cik: z.string(), // Central Index Key (CIK) identifier
    filingDate: z.string(), // Filing date of the report
    acceptedDate: z.string(), // Accepted date of the report
    fiscalYear: z.string(), // Fiscal year of the report
    period: z.string(), // Reporting period (e.g., FY, Q1, etc.)
    revenue: z.number(), // Total revenue
    costOfRevenue: z.number(), // Cost of revenue
    grossProfit: z.number(), // Gross profit
    researchAndDevelopmentExpenses: z.number(), // R&D expenses
    generalAndAdministrativeExpenses: z.number(), // General and administrative expenses
    sellingAndMarketingExpenses: z.number(), // Selling and marketing expenses
    sellingGeneralAndAdministrativeExpenses: z.number(), // SG&A expenses
    otherExpenses: z.number(), // Other expenses
    operatingExpenses: z.number(), // Total operating expenses
    costAndExpenses: z.number(), // Total cost and expenses
    netInterestIncome: z.number(), // Net interest income
    interestIncome: z.number(), // Interest income
    interestExpense: z.number(), // Interest expense
    depreciationAndAmortization: z.number(), // Depreciation and amortization
    ebitda: z.number(), // EBITDA
    ebit: z.number(), // EBIT
    nonOperatingIncomeExcludingInterest: z.number(), // Non-operating income excluding interest
    operatingIncome: z.number(), // Operating income
    totalOtherIncomeExpensesNet: z.number(), // Total other income/expenses (net)
    incomeBeforeTax: z.number(), // Income before tax
    incomeTaxExpense: z.number(), // Income tax expense
    netIncomeFromContinuingOperations: z.number(), // Net income from continuing operations
    netIncomeFromDiscontinuedOperations: z.number(), // Net income from discontinued operations
    otherAdjustmentsToNetIncome: z.number(), // Other adjustments to net income
    netIncome: z.number(), // Net income
    netIncomeDeductions: z.number(), // Net income deductions
    bottomLineNetIncome: z.number(), // Bottom-line net income
    eps: z.number(), // Earnings per share (basic)
    epsDiluted: z.number(), // Earnings per share (diluted)
    weightedAverageShsOut: z.number(), // Weighted average shares outstanding (basic)
    weightedAverageShsOutDil: z.number(), // Weighted average shares outstanding (diluted)
  })
);

export const cashflowStatementDataSchema = z.array(
  z.object({
    date: z.string(), // Date of the report
    symbol: z.string(), // Stock symbol
    reportedCurrency: z.string(), // Currency used in the report
    cik: z.string(), // Central Index Key (CIK) identifier
    filingDate: z.string(), // Filing date of the report
    acceptedDate: z.string(), // Accepted date of the report
    fiscalYear: z.string(), // Fiscal year of the report
    period: z.string(), // Reporting period (e.g., FY, Q1, etc.)
    netIncome: z.number(), // Net income
    depreciationAndAmortization: z.number(), // Depreciation and amortization
    deferredIncomeTax: z.number(), // Deferred income tax
    stockBasedCompensation: z.number(), // Stock-based compensation
    changeInWorkingCapital: z.number(), // Change in working capital
    accountsReceivables: z.number(), // Change in accounts receivables
    inventory: z.number(), // Change in inventory
    accountsPayables: z.number(), // Change in accounts payables
    otherWorkingCapital: z.number(), // Change in other working capital
    otherNonCashItems: z.number(), // Other non-cash items
    netCashProvidedByOperatingActivities: z.number(), // Net cash provided by operating activities
    investmentsInPropertyPlantAndEquipment: z.number(), // Investments in property, plant, and equipment
    acquisitionsNet: z.number(), // Net acquisitions
    purchasesOfInvestments: z.number(), // Purchases of investments
    salesMaturitiesOfInvestments: z.number(), // Sales/maturities of investments
    otherInvestingActivities: z.number(), // Other investing activities
    netCashProvidedByInvestingActivities: z.number(), // Net cash provided by investing activities
    netDebtIssuance: z.number(), // Net debt issuance
    longTermNetDebtIssuance: z.number(), // Long-term net debt issuance
    shortTermNetDebtIssuance: z.number(), // Short-term net debt issuance
    netStockIssuance: z.number(), // Net stock issuance
    netCommonStockIssuance: z.number(), // Net common stock issuance
    commonStockIssuance: z.number(), // Common stock issuance
    commonStockRepurchased: z.number(), // Common stock repurchased
    netPreferredStockIssuance: z.number(), // Net preferred stock issuance
    netDividendsPaid: z.number(), // Net dividends paid
    commonDividendsPaid: z.number(), // Common dividends paid
    preferredDividendsPaid: z.number(), // Preferred dividends paid
    otherFinancingActivities: z.number(), // Other financing activities
    netCashProvidedByFinancingActivities: z.number(), // Net cash provided by financing activities
    effectOfForexChangesOnCash: z.number(), // Effect of foreign exchange changes on cash
    netChangeInCash: z.number(), // Net change in cash
    cashAtEndOfPeriod: z.number(), // Cash at the end of the period
    cashAtBeginningOfPeriod: z.number(), // Cash at the beginning of the period
    operatingCashFlow: z.number(), // Operating cash flow
    capitalExpenditure: z.number(), // Capital expenditure
    freeCashFlow: z.number(), // Free cash flow
    incomeTaxesPaid: z.number(), // Income taxes paid
    interestPaid: z.number(), // Interest paid
  })
);

// Helper function to sum numeric fields across quarters
function sumNumericFields<T extends Record<string, any>>(
  data: T[],
  excludeFields: Set<string> = new Set()
): Partial<T> {
  if (data.length === 0) return {} as Partial<T>;

  const result: any = {};
  const firstItem = data[0];

  // Iterate through all keys in the first item
  for (const key in firstItem) {
    if (excludeFields.has(key)) continue;

    const value = firstItem[key];
    // Only sum numeric fields
    if (typeof value === "number") {
      result[key] = data.reduce((sum, item) => sum + (item[key] as number), 0);
    }
  }

  return result;
}

// Helper function to extract metadata fields from most recent quarter
function extractMetadata<T extends Record<string, any>>(
  mostRecent: T
): Partial<T> {
  const metadata: any = {};
  const metadataFields = [
    "date",
    "symbol",
    "reportedCurrency",
    "cik",
    "filingDate",
    "acceptedDate",
    "fiscalYear",
  ];

  for (const field of metadataFields) {
    if (field in mostRecent) {
      metadata[field] = mostRecent[field];
    }
  }

  metadata.period = "TTM";
  return metadata;
}

export async function fetchFinancialReportData(symbol: string) {
  const fmpApiKey = process.env.FMP_API_KEY;
  const baseURL = process.env.FMP_BASE_URL;

  if (!fmpApiKey || !baseURL) {
    console.error("FMP API Key or Base URL is not set in .env.local");
    return null;
  }

  // Define the URLs for the API calls
  const urls = {
    balanceSheet: `${baseURL}balance-sheet-statement?symbol=${symbol}&period=quarter&limit=1&apikey=${fmpApiKey}`,
    incomeStatement: `${baseURL}income-statement?symbol=${symbol}&period=quarter&limit=4&apikey=${fmpApiKey}`,
    cashflowStatement: `${baseURL}cash-flow-statement?symbol=${symbol}&period=quarter&limit=4&apikey=${fmpApiKey}`,
  };

  // start fetching data
  try {
    // Fetch all data in parallel
    const balanceSheetResponse = await fetch(urls.balanceSheet);
    const balanceSheetData = await balanceSheetResponse.json();
    const validatedBalanceSheetData =
      balanceSheetDataSchema.parse(balanceSheetData);

    // Fetch income statement data
    const incomeStatementResponse = await fetch(urls.incomeStatement);
    const incomeStatementData = await incomeStatementResponse.json();
    const validatedIncomeStatementData =
      incomeStatementDataSchema.parse(incomeStatementData);

    // Aggregate quarterly data to form TTM (Trailing Twelve Months) income statement
    if (validatedIncomeStatementData.length < 4) {
      console.error(
        "Not enough quarterly data to calculate TTM",
        urls.incomeStatement
      );
      return null;
    }

    const mostRecentQuarter = validatedIncomeStatementData[0];

    // Fields that should NOT be summed (use most recent quarter instead)
    const incomeExcludeFromSum = new Set([
      "eps",
      "epsDiluted",
      "weightedAverageShsOut",
      "weightedAverageShsOutDil",
    ]);

    const ttmIncomeStatement = {
      ...extractMetadata(mostRecentQuarter),
      ...sumNumericFields(validatedIncomeStatementData, incomeExcludeFromSum),
      // Per-share metrics from most recent quarter
      eps: mostRecentQuarter.eps,
      epsDiluted: mostRecentQuarter.epsDiluted,
      weightedAverageShsOut: mostRecentQuarter.weightedAverageShsOut,
      weightedAverageShsOutDil: mostRecentQuarter.weightedAverageShsOutDil,
    };

    // Fetch cashflow statement data
    const cashflowStatementResponse = await fetch(urls.cashflowStatement);
    const cashflowStatementData = await cashflowStatementResponse.json();
    const validatedCashflowStatementData = cashflowStatementDataSchema.parse(
      cashflowStatementData
    );

    // Aggregate balance sheet - use most recent quarter (balance sheet is a snapshot, not cumulative)
    if (validatedBalanceSheetData.length < 1) {
      console.error("No balance sheet data available", urls.balanceSheet);
      return null;
    }
    const mostRecentBalanceSheet = validatedBalanceSheetData[0];
    const ttmBalanceSheet = {
      ...mostRecentBalanceSheet,
      period: "TTM",
    };

    // Aggregate cashflow statement - sum across 4 quarters
    if (validatedCashflowStatementData.length < 4) {
      console.error(
        "Not enough quarterly data to calculate TTM for cashflow",
        urls.cashflowStatement
      );
      return null;
    }

    const mostRecentCashflow = validatedCashflowStatementData[0];
    const oldestCashflow =
      validatedCashflowStatementData[validatedCashflowStatementData.length - 1];

    // Fields that should NOT be summed (use specific values instead)
    const cashflowExcludeFromSum = new Set([
      "cashAtEndOfPeriod",
      "cashAtBeginningOfPeriod",
    ]);

    const ttmCashflowStatement = {
      ...extractMetadata(mostRecentCashflow),
      ...sumNumericFields(
        validatedCashflowStatementData,
        cashflowExcludeFromSum
      ),
      // Point-in-time values
      cashAtEndOfPeriod: mostRecentCashflow.cashAtEndOfPeriod,
      cashAtBeginningOfPeriod: oldestCashflow.cashAtBeginningOfPeriod,
    };

    return {
      balanceSheet: ttmBalanceSheet,
      incomeStatement: ttmIncomeStatement,
      cashflowStatement: ttmCashflowStatement,
    };
  } catch (error) {
    console.error("Error fetching financial data:", error);
    return null;
  }
}

// export a type for the return value of fetchFinancialReportData
export type TTMFinancialReportData = Awaited<
  ReturnType<typeof fetchFinancialReportData>
>;

// export a schema to validate the return value of fetchFinancialReportData
export const ttmFinancialReportDataSchema = z.object({
  balanceSheet: balanceSheetDataSchema,
  incomeStatement: incomeStatementDataSchema,
  cashflowStatement: cashflowStatementDataSchema,
});
