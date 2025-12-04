// Simple Node.js test without TypeScript compilation
const prisma = require("@repo/db").default;

async function testDbSave() {
  console.log("Starting DB Save Test...");

  const traceId = `test-${Date.now()}`;
  const analysisResult = {
    id: traceId,
    symbol: "TEST_AAPL",
    price: 150,
    score: 0,
    tier: "Tier 1",
    moat: "Network Effect",
    valuationStatus: "Undervalued",
    thesis: {
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
    },
    dcf: {
      intrinsicValuePerShare: 200,
      upsideDownside: 33,
      assumptions: {
        revenueGrowthRates: [],
        terminalGrowthRate: 0.02,
        discountRate: 0.08,
      },
      projections: [],
    },
    financials: {
      revenue: 1000000,
      netIncome: 0,
      fcf: 200000,
      netDebt: 50000,
    },
  };

  console.log(
    "Constructed Analysis Result:",
    JSON.stringify(analysisResult, null, 2)
  );

  try {
    console.log("Saving to DB...");
    const result = await prisma.analysisResult.create({ data: analysisResult });
    console.log("✅ Successfully saved to DB:", result.id);

    console.log("Cleaning up...");
    await prisma.analysisResult.delete({ where: { id: traceId } });
    console.log("✅ Cleanup complete.");
  } catch (error) {
    console.error("❌ Error:", error.message);
    console.error("Stack:", error.stack);
  } finally {
    await prisma.$disconnect();
  }
}

testDbSave();
