import { z } from "zod";
import type { InternalStateManager } from "motia";

/**
 * Generic hook to retrieve and validate state data with proper error handling
 *
 * @param stateKey - The key used to store data in state
 * @param schema - Zod schema to validate the data
 * @param state - Motia state manager
 * @param traceId - Trace ID for logging
 * @param logger - Logger instance for error reporting (optional)
 * @returns Validated data conforming to the schema
 * @throws Error if data is missing or validation fails
 */
export async function getValidatedState<T extends z.ZodTypeAny>(
  stateKey: string,
  schema: T,
  state: InternalStateManager,
  traceId: string,
  logger?: {
    error: (message: string, meta: any) => void;
    info?: (message: string, meta?: any) => void;
  }
): Promise<z.infer<T>> {
  // Retrieve data from state
  const data = await state.get(stateKey, traceId);

  // Check if data exists
  if (!data) {
    const errorMsg = `Missing required state data: ${stateKey}`;
    if (logger) {
      logger.error(errorMsg, { traceId, stateKey });
    }
    throw new Error(errorMsg);
  }

  // Validate with Zod schema
  const validation = schema.safeParse(data);

  if (!validation.success) {
    const errorDetails = validation.error.issues
      .map((e) => `${e.path.join(".")}: ${e.message}`)
      .join(", ");

    const errorMsg = `Invalid ${stateKey} data structure: ${errorDetails}`;

    if (logger) {
      logger.error(`Invalid ${stateKey} data structure`, {
        traceId,
        stateKey,
        errors: validation.error.issues,
      });
    }

    throw new Error(errorMsg);
  }

  // Return validated data
  return validation.data;
}

/**
 * Batch retrieve and validate multiple state keys
 *
 * @param stateConfigs - Array of {key, schema} configurations
 * @param state - Motia state manager
 * @param traceId - Trace ID
 * @param logger - Logger instance (optional)
 * @returns Object with validated data for each key
 */
export async function getValidatedStates<
  T extends Record<string, z.ZodTypeAny>
>(
  stateConfigs: { key: string; schema: z.ZodTypeAny }[],
  state: InternalStateManager,
  traceId: string,
  logger?: {
    error: (message: string, meta: any) => void;
    info?: (message: string, meta?: any) => void;
  }
): Promise<Record<string, any>> {
  const results: Record<string, any> = {};

  for (const config of stateConfigs) {
    results[config.key] = await getValidatedState(
      config.key,
      config.schema,
      state,
      traceId,
      logger
    );
  }

  return results;
}
