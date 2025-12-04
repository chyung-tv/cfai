async function testDbSave() {
  console.log("Starting DB Save Test...");

  // Mock Data
  const traceId = `test-${Date.now()}`;
  const symbol = "TEST_AAPL";

  const mockReverseDcfData = {
    currentPrice: 150,
    ttmRevenue: 1000000,
    ttmFreeCashFlow: 200000,
    netDebt: 50000,
  };

  const mockRatingData = {
    tier: { classification: "Tier 1" },
    economicMoat: { primaryMoat: "Network Effect" },
  };

  const mockGrowthJudgementData = {
    verdict: "Undervalued",
  };

  const mockStructuredThesis = {
    executiveSummary: "Test Summary",
    businessProfile: { essence: "Test Essence", moat: "Test Moat" },
    porter: {
      threatOfEntrants: "Low",
      bargainingPowerSuppliers: "Low",
      bargainingPowerBuyers: "Low",
      threatOfSubstitutes: "Low",
      competitiveRivalry: "Low",
    },
    drivers: {
      externalTailwinds: "None",
      externalHeadwinds: "None",
      internalCatalysts: "None",
      internalDrags: "None",
    },
    managementProfile: { leadership: "Good", compensationAlignment: "Good" },
    industryProfile: {
      growthProjections: 0.05,
      trends: "Up",
      competition: "Low",
    },
    recentDevelopments: "None",
  };

  const mockDcfData = {
    intrinsicValuePerShare: 200,
    upsideDownside: 33,
    assumptions: {
      revenueGrowthRates: [],
      terminalGrowthRate: 0.02,
      discountRate: 0.08,
    },
    projections: [],
  };

  const analysisResult = {
    id: traceId,
    symbol,
    price: mockReverseDcfData.currentPrice,
    score: 0,
    tier: mockRatingData.tier.classification,
    moat: mockRatingData.economicMoat.primaryMoat,
    valuationStatus: mockGrowthJudgementData.verdict,
    thesis: mockStructuredThesis,
    dcf: mockDcfData,
    financials: {
      revenue: mockReverseDcfData.ttmRevenue,
      netIncome: 0,
      fcf: mockReverseDcfData.ttmFreeCashFlow,
      netDebt: mockReverseDcfData.netDebt,
    },
  };

  console.log(
    "Constructed Analysis Result:",
    JSON.stringify(analysisResult, null, 2)
  );

  try {
    console.log("Importing Prisma...");
    // Use CommonJS require instead of dynamic import for ts-node compatibility
    const prisma = require("@repo/db").default;

    console.log("Saving to DB...");
    const result = await prisma.analysisResult.create({
      data: {
        ...analysisResult,
        thesis: analysisResult.thesis as any,
        dcf: analysisResult.dcf as any,
        financials: analysisResult.financials as any,
      },
    });
    console.log("✅ Successfully saved to DB:", result);

    // Cleanup
    console.log("Cleaning up...");
    await prisma.analysisResult.delete({ where: { id: traceId } });
    console.log("✅ Cleanup complete.");
  } catch (error) {
    console.error("❌ Error saving to DB:", error);
  }
}

testDbSave();
