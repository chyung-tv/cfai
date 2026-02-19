import { auth } from "@/lib/auth";
import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:3001";
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ traceId: string }> }
) {
  const session = await auth();
  if (!session?.user) {
    return new Response("Unauthorized", { status: 401 });
  }

  if (!BACKEND_API_KEY) {
    console.error("BACKEND_API_KEY not configured");
    return new Response("Server misconfiguration", { status: 500 });
  }

  const { traceId } = await params;
  if (!traceId) {
    return new Response("traceId required", { status: 400 });
  }

  const backendStreamUrl = `${BACKEND_URL}/analysis/${traceId}/stream`;
  const backendRes = await fetch(backendStreamUrl, {
    headers: {
      "X-API-Key": BACKEND_API_KEY,
    },
    cache: "no-store",
  });

  if (!backendRes.ok) {
    return new Response("Backend error", { status: backendRes.status });
  }

  return new Response(backendRes.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
