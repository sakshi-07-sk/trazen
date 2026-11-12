import crypto from "crypto";
import {
  AdminAuditEntry,
  PublicUser,
  UserRecord,
  UserRole,
  UserStatus,
} from "./types";
import { hashPassword } from "./password";

interface AuthStoreState {
  users: Map<string, UserRecord>;
  auditLogs: AdminAuditEntry[];
  resetTokens: Map<string, { email: string; expiresAt: number }>;
}

function seedDemoUsers(users: Map<string, UserRecord>, auditLogs: AdminAuditEntry[]) {
  if (process.env.NODE_ENV === "production" && process.env.ENABLE_DEMO_ACCOUNTS !== "true") {
    return;
  }

  const adminPass = process.env.DEMO_ADMIN_PASSWORD || "AdminTrace!2025";
  const invPass = process.env.DEMO_INVESTIGATOR_PASSWORD || "Investigator!2025";
  const analystPass = process.env.DEMO_ANALYST_PASSWORD || "Analyst!2025";

  const now = new Date().toISOString();
  const seeds: UserRecord[] = [
    {
      id: "usr-admin-01",
      fullName: "Elena Vance",
      email: "admin@cryptotrace.io",
      passwordHash: hashPassword(adminPass),
      role: "ADMIN",
      organization: "CryptoTrace Security Ops",
      status: "ACTIVE",
      createdAt: "2025-01-10T08:00:00.000Z",
      lastLoginAt: now,
    },
    {
      id: "usr-inv-01",
      fullName: "Marcus Thorne",
      email: "investigator@cryptotrace.io",
      passwordHash: hashPassword(invPass),
      role: "INVESTIGATOR",
      organization: "FinCrime Tracing Unit",
      status: "ACTIVE",
      createdAt: "2025-01-15T10:30:00.000Z",
      lastLoginAt: now,
    },
    {
      id: "usr-ana-01",
      fullName: "Aria Chen",
      email: "analyst@cryptotrace.io",
      passwordHash: hashPassword(analystPass),
      role: "ANALYST",
      organization: "Threat Intelligence Lab",
      status: "ACTIVE",
      createdAt: "2025-02-01T14:15:00.000Z",
      lastLoginAt: now,
    },
  ];

  for (const u of seeds) {
    users.set(u.email.toLowerCase(), u);
  }

  auditLogs.push(
    {
      id: "aud-001",
      timestamp: "2025-02-12T09:15:00.000Z",
      actorEmail: "admin@cryptotrace.io",
      actorRole: "ADMIN",
      action: "RBAC_POLICY_INITIALIZED",
      target: "SYSTEM",
      details: "Initialized role-based access control policy for Admin, Investigator, and Analyst tiers.",
    },
    {
      id: "aud-002",
      timestamp: "2025-02-12T11:42:00.000Z",
      actorEmail: "investigator@cryptotrace.io",
      actorRole: "INVESTIGATOR",
      action: "INVESTIGATION_TRACED",
      target: "CT-CASE-2024-8841",
      details: "Executed 3-hop ETH/ERC-20 trace and sealed SHA-256 evidence chain.",
    },
    {
      id: "aud-003",
      timestamp: "2025-02-12T13:10:00.000Z",
      actorEmail: "analyst@cryptotrace.io",
      actorRole: "ANALYST",
      action: "RISK_THRESHOLD_EVALUATED",
      target: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
      details: "Flagged peel-chain decay and mixer exposure with confidence cap applied.",
    }
  );
}

function getStore(): AuthStoreState {
  const g = globalThis as unknown as { __cryptotraceAuthStore?: AuthStoreState };
  if (!g.__cryptotraceAuthStore) {
    const users = new Map<string, UserRecord>();
    const auditLogs: AdminAuditEntry[] = [];
    const resetTokens = new Map<string, { email: string; expiresAt: number }>();
    seedDemoUsers(users, auditLogs);
    g.__cryptotraceAuthStore = { users, auditLogs, resetTokens };
  }
  return g.__cryptotraceAuthStore;
}

export function sanitizeUser(user: UserRecord): PublicUser {
  const { passwordHash: _ignored, ...rest } = user;
  void _ignored;
  return rest;
}

export function findUserByEmail(email: string): UserRecord | undefined {
  return getStore().users.get(email.trim().toLowerCase());
}

export function findUserById(id: string): UserRecord | undefined {
  for (const user of Array.from(getStore().users.values())) {
    if (user.id === id) return user;
  }
  return undefined;
}

export function listUsers(): PublicUser[] {
  return Array.from(getStore().users.values()).map(sanitizeUser);
}

export function createUser(params: {
  fullName: string;
  email: string;
  password: string;
  role: UserRole;
  organization: string;
}): UserRecord {
  const store = getStore();
  const normalizedEmail = params.email.trim().toLowerCase();
  if (store.users.has(normalizedEmail)) {
    throw new Error("EMAIL_EXISTS");
  }
  const user: UserRecord = {
    id: `usr-${crypto.randomUUID().slice(0, 8)}`,
    fullName: params.fullName.trim(),
    email: normalizedEmail,
    passwordHash: hashPassword(params.password),
    role: params.role,
    organization: params.organization.trim(),
    status: "ACTIVE",
    createdAt: new Date().toISOString(),
  };
  store.users.set(normalizedEmail, user);
  return user;
}

export function updateUserById(
  id: string,
  patch: { role?: UserRole; status?: UserStatus; lastLoginAt?: string }
): PublicUser | null {
  const store = getStore();
  for (const [key, user] of Array.from(store.users.entries())) {
    if (user.id === id) {
      const updated: UserRecord = {
        ...user,
        ...patch,
      };
      store.users.set(key, updated);
      return sanitizeUser(updated);
    }
  }
  return null;
}

export function recordAudit(entry: Omit<AdminAuditEntry, "id" | "timestamp">): AdminAuditEntry {
  const store = getStore();
  const full: AdminAuditEntry = {
    id: `aud-${crypto.randomUUID().slice(0, 8)}`,
    timestamp: new Date().toISOString(),
    ...entry,
  };
  store.auditLogs.unshift(full);
  if (store.auditLogs.length > 250) {
    store.auditLogs.length = 250;
  }
  return full;
}

export function listAuditLogs(): AdminAuditEntry[] {
  return [...getStore().auditLogs];
}

export function createResetToken(email: string): string | null {
  const user = findUserByEmail(email);
  if (!user) return null;
  const token = crypto.randomBytes(24).toString("hex");
  getStore().resetTokens.set(token, {
    email: user.email,
    expiresAt: Date.now() + 15 * 60 * 1000,
  });
  return token;
}
