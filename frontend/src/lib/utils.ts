import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formats snake_case text to Title Case
 * @param text - Snake case string (e.g., "high_quality")
 * @returns Title cased string (e.g., "High Quality")
 */
export function formatSnakeCase(text: string): string {
  return text
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
