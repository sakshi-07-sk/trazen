import { InvestigationCase } from "@/types/investigation";

// In-memory store for imported batches across route invocations
const globalForImported = globalThis as unknown as {
  _importedCasesStore?: Map<string, InvestigationCase>;
};

export const importedCasesStore =
  globalForImported._importedCasesStore ?? new Map<string, InvestigationCase>();

if (process.env.NODE_ENV !== "production") {
  globalForImported._importedCasesStore = importedCasesStore;
}
