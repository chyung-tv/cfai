import { PrismaClient } from "@prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";
import { Pool } from "pg";

// Load .env from monorepo root for backend usage
// Next.js will handle this automatically, but Motia/backend needs explicit loading
if (!process.env.DATABASE_URL) {
  try {
    const dotenv = require("dotenv");
    const path = require("path");
    const fs = require("fs");

    // Try to find .env file by walking up directories
    let currentDir = __dirname;
    let envPath: string | null = null;

    for (let i = 0; i < 5; i++) {
      const testPath = path.join(currentDir, ".env");
      if (fs.existsSync(testPath)) {
        envPath = testPath;
        break;
      }
      currentDir = path.dirname(currentDir);
    }

    if (envPath) {
      dotenv.config({ path: envPath });
    }
  } catch (e) {
    // Ignore errors in browser/edge environments
  }
}

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error(
    "DATABASE_URL is not defined. Make sure you have a .env file in the root of your project."
  );
}

const pool = new Pool({ connectionString });
const adapter = new PrismaPg(pool);

const prismaClientSingleton = () => {
  return new PrismaClient({ adapter });
};

declare const globalThis: {
  prismaGlobal: ReturnType<typeof prismaClientSingleton>;
} & typeof global;

const prisma = globalThis.prismaGlobal ?? prismaClientSingleton();

export default prisma;

if (process.env.NODE_ENV !== "production") globalThis.prismaGlobal = prisma;

export * from "@prisma/client";
