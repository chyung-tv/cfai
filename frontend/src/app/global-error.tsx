"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global error:", error);
  }, [error]);

  return (
    <html>
      <body>
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <h1>Critical Error</h1>
          <p>The application encountered a critical error.</p>
          <button onClick={reset}>Try Again</button>
        </div>
      </body>
    </html>
  );
}
