import type { NextConfig } from "next";
import path from "path";

// Load environment variables from monorepo root
import { config } from "dotenv";
config({ path: path.resolve(__dirname, "../../.env") });

const nextConfig: NextConfig = {
  /* config options here */
  serverExternalPackages: ["@repo/db"],
};

export default nextConfig;
