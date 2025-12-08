type LogLevel = "info" | "warn" | "error" | "debug";

class Logger {
  private isDevelopment = process.env.NODE_ENV === "development";

  private log(level: LogLevel, message: string, meta?: any) {
    if (!this.isDevelopment && level === "debug") return;

    const timestamp = new Date().toISOString();
    const logData = { timestamp, level, message, ...meta };

    if (this.isDevelopment) {
      console[level === "debug" ? "log" : level](
        `[${level.toUpperCase()}]`,
        message,
        meta || ""
      );
    } else {
      // In production, only log errors
      if (level === "error") {
        console.error(JSON.stringify(logData));
      }
    }
  }

  info(message: string, meta?: any) {
    this.log("info", message, meta);
  }

  warn(message: string, meta?: any) {
    this.log("warn", message, meta);
  }

  error(message: string, meta?: any) {
    this.log("error", message, meta);
  }

  debug(message: string, meta?: any) {
    this.log("debug", message, meta);
  }
}

export const logger = new Logger();
