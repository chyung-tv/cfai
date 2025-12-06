"use client";

import { MotiaStreamProvider } from "@motiadev/stream-client-react";
import { SessionProvider } from "next-auth/react";
import { Toaster } from "sonner";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <MotiaStreamProvider address="ws://localhost:3001">
        {children}
        <Toaster />
      </MotiaStreamProvider>
    </SessionProvider>
  );
}
