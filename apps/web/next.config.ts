import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["@repo/db"],
  eslint: {
    ignoreDuringBuilds: true, // ESLint config resolution can fail in some environments
  },
};

export default nextConfig;
