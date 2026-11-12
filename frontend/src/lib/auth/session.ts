import { SessionPayload, UserRole } from "./types";

export const SESSION_COOKIE_NAME = "cryptotrace_session";

function getSecret(): string {
  if (process.env.SESSION_SECRET && process.env.SESSION_SECRET.length >= 16) {
    return process.env.SESSION_SECRET;
  }
  const g = globalThis as unknown as { __cryptotraceSessionSecret?: string };
  if (!g.__cryptotraceSessionSecret) {
    // Ephemeral process secret for local/dev when SESSION_SECRET is not configured
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    g.__cryptotraceSessionSecret = Array.from(bytes, (b) =>
      b.toString(16).padStart(2, "0")
    ).join("");
  }
  return g.__cryptotraceSessionSecret;
}

function toBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(str: string): Uint8Array {
  const padded = str.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((str.length + 3) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function importHmacKey(secret: string): Promise<CryptoKey> {
  const enc = new TextEncoder();
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

export async function signSessionToken(
  payload: Omit<SessionPayload, "iat" | "exp">,
  ttlSeconds = 60 * 60 * 12
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const fullPayload: SessionPayload = {
    ...payload,
    iat: now,
    exp: now + ttlSeconds,
  };
  const enc = new TextEncoder();
  const dataPart = toBase64Url(enc.encode(JSON.stringify(fullPayload)));
  const key = await importHmacKey(getSecret());
  const sigBuffer = await crypto.subtle.sign("HMAC", key, enc.encode(dataPart));
  const sigPart = toBase64Url(new Uint8Array(sigBuffer));
  return `${dataPart}.${sigPart}`;
}

export async function verifySessionToken(
  token: string | undefined | null
): Promise<SessionPayload | null> {
  if (!token || !token.includes(".")) return null;
  const [dataPart, sigPart] = token.split(".");
  if (!dataPart || !sigPart) return null;

  try {
    const enc = new TextEncoder();
    const key = await importHmacKey(getSecret());
    const sigBytes = fromBase64Url(sigPart);
    const valid = await crypto.subtle.verify(
      "HMAC",
      key,
      sigBytes.buffer as ArrayBuffer,
      enc.encode(dataPart)
    );
    if (!valid) return null;

    const json = new TextDecoder().decode(fromBase64Url(dataPart));
    const parsed = JSON.parse(json) as SessionPayload;
    const now = Math.floor(Date.now() / 1000);
    if (!parsed.exp || parsed.exp < now) return null;
    if (!parsed.userId || !parsed.role || !parsed.email) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function getDashboardPathForRole(role: UserRole): string {
  switch (role) {
    case "ADMIN":
      return "/admin/dashboard";
    case "INVESTIGATOR":
      return "/investigator/dashboard";
    case "ANALYST":
      return "/analyst/dashboard";
  }
}
