import { fetchFinancialReportData } from "../steps/lib/functions/ttmReport";

console.log("Starting minimal test...");

async function run() {
  try {
    console.log("Calling fetchFinancialReportData...");
    const data = await fetchFinancialReportData("AAPL");
    console.log("Data fetched:", data ? "Yes" : "No");
  } catch (e) {
    console.error("Error:", e);
  }
}

run();
