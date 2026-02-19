import { config } from "@motiadev/core";
import endpointPlugin from "@motiadev/plugin-endpoint/plugin";
import logsPlugin from "@motiadev/plugin-logs/plugin";
import observabilityPlugin from "@motiadev/plugin-observability/plugin";
import statesPlugin from "@motiadev/plugin-states/plugin";
import bullmqPlugin from "@motiadev/plugin-bullmq/plugin";
import { RedisStateAdapter } from "@motiadev/adapter-redis-state";
import { apiKeyMiddleware } from "./middlewares/api-key.middleware";
import { createStatusSubscriber } from "./lib/status-stream";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

export default config({
  plugins: [observabilityPlugin, statesPlugin, endpointPlugin, logsPlugin, bullmqPlugin],
  adapters: {
    state: new RedisStateAdapter(
      { url: REDIS_URL },
      { keyPrefix: "cfai:state:", ttl: 86400 }
    ),
  },
  app: (app) => {
    // API key protection - all backend routes require valid X-API-Key
    app.use(apiKeyMiddleware);

    // SSE endpoint for analysis task status (replaces WebSocket stream)
    app.get("/analysis/:traceId/stream", async (req, res) => {
      const { traceId } = req.params;
      if (!traceId) {
        res.status(400).json({ error: "traceId required" });
        return;
      }

      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");
      res.setHeader("X-Accel-Buffering", "no");
      res.flushHeaders();

      const sendEvent = (data: object) => {
        res.write(`data: ${JSON.stringify(data)}\n\n`);
      };

      let unsubscribe: (() => Promise<void>) | null = null;

      try {
        unsubscribe = await createStatusSubscriber(traceId, (event) => {
          sendEvent(event);
        });
      } catch (err) {
        console.error("SSE subscribe error:", err);
        sendEvent({ error: "Failed to subscribe" });
        res.end();
        return;
      }

      req.on("close", () => {
        unsubscribe?.().catch(() => {});
        res.end();
      });
    });
  },
});
