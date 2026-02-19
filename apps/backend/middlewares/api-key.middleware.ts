/**
 * API Key middleware - protects all backend endpoints.
 * Only requests with valid X-API-Key header are allowed.
 * Next.js server includes this header when calling the backend.
 */

import type { Request, Response, NextFunction } from "express";

const HEADER_NAME = "x-api-key";

export function apiKeyMiddleware(req: Request, res: Response, next: NextFunction): void {
  const key = process.env.BACKEND_API_KEY;
  if (!key) {
    console.error("BACKEND_API_KEY not configured");
    res.status(500).json({ error: "Server misconfiguration" });
    return;
  }

  const provided = req.headers[HEADER_NAME] ?? req.headers["authorization"]?.replace(/^Bearer\s+/i, "");
  if (provided !== key) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }

  next();
}
