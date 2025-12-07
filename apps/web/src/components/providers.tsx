"use client";

import { MotiaStreamProvider } from "@motiadev/stream-client-react";
import { SessionProvider } from "next-auth/react";
import { Toaster } from "sonner";

// WebSocket URL for Motia Streams
// Local: ws://localhost:3001
// Production: wss://your-project.motia.cloud (from Motia Cloud dashboard)
const STREAM_WS_URL =
  process.env.NEXT_PUBLIC_BACKEND_WS_URL || "ws://localhost:3001";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <MotiaStreamProvider address={STREAM_WS_URL}>
        {children}
        <Toaster />
      </MotiaStreamProvider>
    </SessionProvider>
  );
}
