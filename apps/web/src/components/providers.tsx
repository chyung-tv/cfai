"use client";

import { MotiaStreamProvider } from "@motiadev/stream-client-react";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <MotiaStreamProvider address="ws://localhost:3001">
      {children}
    </MotiaStreamProvider>
  );
}
