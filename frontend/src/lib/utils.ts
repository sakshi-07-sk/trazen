import { ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatAddress(address: string, start = 6, end = 4): string {
  if (!address) return "";
  if (address.length <= start + end) return address;
  return `${address.substring(0, start)}...${address.substring(address.length - end)}`;
}

export const truncateAddress = formatAddress;

export function formatHash(hash: string, start = 8, end = 6): string {
  if (!hash) return "";
  if (hash.length <= start + end) return hash;
  return `${hash.substring(0, start)}...${hash.substring(hash.length - end)}`;
}

export function formatCurrency(amount: number, symbol = "ETH", decimals = 4): string {
  if (isNaN(amount)) return `0.00 ${symbol}`;
  return `${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: decimals })} ${symbol}`;
}

export function formatUSD(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatTimestamp(timestamp: string | number): string {
  const date = typeof timestamp === "string" ? new Date(timestamp) : new Date(timestamp * 1000);
  return date.toISOString().replace("T", " ").substring(0, 19) + " UTC";
}

export function getCaseRiskScore(c: {
  nodes: { riskScore: number }[];
  findings: { severity: string }[];
}): number {
  if (c.nodes.length > 0) {
    return Math.max(...c.nodes.map((n) => n.riskScore));
  }
  return c.findings.some((f) => f.severity === "CRITICAL") ? 90 : 50;
}

export function getCaseConfidence(c: {
  receivers: { attributionConfidence: number }[];
  findings: { confidence: number }[];
}): number {
  if (c.receivers.length > 0) {
    return Math.round(c.receivers[0].attributionConfidence);
  }
  if (c.findings.length > 0) {
    return Math.round(
      c.findings.reduce((acc, f) => acc + f.confidence, 0) / c.findings.length
    );
  }
  return 0;
}
