import { performCustomDCF } from "../steps/lib/functions/dcf";
import { reverseDcf } from "../steps/lib/functions/reverse-dcf";
import { fetchFinancialReportData } from "../steps/lib/functions/ttmReport";
import { fetchQuote } from "../steps/lib/functions/quote";

console.log("Starting test script...");

async function testBackendFunctions() {
  const symbol = "AAPL";
  console.log(`\n=== Testing Backend Functions for ${symbol} ===\n`);

  // 0. Test Quote Fetching
  console.log("--- 0. Testing fetchQuote ---");
  try {
    const quote = await fetchQuote(symbol);
    console.log("✅ Quote Fetched Successfully");
    console.log("   Price:", quote.price);
    console.log("   Market Cap:", quote.marketCap);
  } catch (error) {
    console.error("❌ Error in fetchQuote:", error);
  }

  // 1. Test TTM Report Fetching
  console.log("--- 1. Testing fetchFinancialReportData ---");
  try {
    const financialData = await fetchFinancialReportData(symbol);
    if (financialData) {
      console.log("✅ Financial Data Fetched Successfully");
      console.log("   Revenue:", financialData.incomeStatement.revenue);
      console.log("   Net Income:", financialData.incomeStatement.netIncome);
      console.log("   FCF:", financialData.cashflowStatement.freeCashFlow);
    } else {
      console.error("❌ Failed to fetch financial data");
    }
  } catch (error) {
    console.error("❌ Error in fetchFinancialReportData:", error);
  }

  // 2. Test Reverse DCF
  console.log("\n--- 2. Testing reverseDcf ---");
  try {
    // Mock data for reverse DCF (using approximate AAPL numbers)
    const mockReverseDcfInput = {
      currentPrice: 230,
      marketCap: 3500000000000,
      sharesOutstanding: 15200000000,
      ttmRevenue: 390000000000,
      ttmFreeCashFlow: 100000000000,
      projectionYears: 5,
      terminalGrowthRate: 0.03,
    };

    const reverseDcfResults = await reverseDcf(mockReverseDcfInput);
    console.log("✅ Reverse DCF Calculated Successfully");
    console.log("   Results count:", reverseDcfResults.length);
    if (reverseDcfResults.length > 0) {
      console.log("   Sample Result:", reverseDcfResults[0]);
    }
  } catch (error) {
    console.error("❌ Error in reverseDcf:", error);
  }

  // 3. Test Forward DCF
  console.log("\n--- 3. Testing performCustomDCF ---");
  try {
    const mockDcfInput = {
      symbol: symbol,
      aiParams: {
        revenueGrowthRates: [
          0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.025, 0.025, 0.025, 0.025,
        ], // 10 years
        terminalGrowthRate: 0.025,
        discountRate: 0.08,
      },
      financials: {
        revenueTTM: 390000000000,
        fcfTTM: 100000000000,
        sharesOutstanding: 15200000000,
        netDebt: -50000000000, // Net cash
      },
    };

    const dcfResult = await performCustomDCF(mockDcfInput);
    if (dcfResult) {
      console.log("✅ Forward DCF Calculated Successfully");
      console.log("   Intrinsic Value:", dcfResult.intrinsicValuePerShare);
      console.log(
        "   Upside/Downside:",
        dcfResult.upsideDownside.toFixed(2) + "%"
      );
    } else {
      console.error("❌ Failed to calculate DCF");
    }
  } catch (error) {
    console.error("❌ Error in performCustomDCF:", error);
  }
}

testBackendFunctions();
