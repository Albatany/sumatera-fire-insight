import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...args: ClassValue[]) {
  return twMerge(clsx(args));
}
export function num(v: unknown) {
  return typeof v === "number" && Number.isFinite(v)
    ? new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(v)
    : "—";
}
export function day(v: unknown) {
  return typeof v === "string" ? v.slice(0, 10) : "—";
}
