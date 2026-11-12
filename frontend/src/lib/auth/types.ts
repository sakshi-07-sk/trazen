export type UserRole = "ADMIN" | "INVESTIGATOR" | "ANALYST";
export type PublicSignupRole = "INVESTIGATOR" | "ANALYST";
export type UserStatus = "ACTIVE" | "DEACTIVATED";

export interface UserRecord {
  id: string;
  fullName: string;
  email: string;
  passwordHash: string;
  role: UserRole;
  organization: string;
  status: UserStatus;
  createdAt: string;
  lastLoginAt?: string;
}

export type PublicUser = Omit<UserRecord, "passwordHash">;

export interface SessionPayload {
  userId: string;
  email: string;
  fullName: string;
  role: UserRole;
  organization: string;
  iat: number;
  exp: number;
}

export interface AdminAuditEntry {
  id: string;
  timestamp: string;
  actorEmail: string;
  actorRole: UserRole | "SYSTEM" | "PUBLIC";
  action: string;
  target: string;
  details: string;
}
