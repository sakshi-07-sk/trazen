"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  BlockchainNetwork,
  InvestigationCase,
  InvestigationStats,
} from "@/types/investigation";
import { MOCK_BTC_CASE, MOCK_ETH_CASE, MOCK_STATS } from "@/lib/mockData";
import { investigationApi } from "@/services/api/investigationApi";

export interface PlatformSettings {
  role1Endpoint: string;
  role2Endpoint: string;
  offlineMode: boolean;
  highRiskThreshold: number;
  defaultGraphLayout: "cose" | "breadthfirst" | "circle";
  defaultHopDepth: number;
  reduceMotion: boolean;
}

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant: "info" | "success" | "warning" | "error";
}

interface ForensicContextValue {
  allCases: InvestigationCase[];
  activeCase: InvestigationCase;
  stats: InvestigationStats;
  networkFilter: "ALL" | BlockchainNetwork;
  setNetworkFilter: (n: "ALL" | BlockchainNetwork) => void;
  globalSearch: string;
  setGlobalSearch: (q: string) => void;
  isOnline: boolean;
  isLoading: boolean;
  error: string | null;
  settings: PlatformSettings;
  updateSettings: (patch: Partial<PlatformSettings>) => void;
  selectCase: (caseId: string) => void;
  addOrActivateCase: (c: InvestigationCase) => void;
  refreshData: () => Promise<void>;
  isCopilotOpen: boolean;
  setIsCopilotOpen: (open: boolean) => void;
  isCommandPaletteOpen: boolean;
  setIsCommandPaletteOpen: (open: boolean) => void;
  toasts: ToastItem[];
  addToast: (toast: Omit<ToastItem, "id">) => void;
  dismissToast: (id: string) => void;
}

const DEFAULT_SETTINGS: PlatformSettings = {
  role1Endpoint: "http://localhost:8000",
  role2Endpoint: "http://localhost:8001",
  offlineMode: false,
  highRiskThreshold: 70,
  defaultGraphLayout: "cose",
  defaultHopDepth: 3,
  reduceMotion: false,
};

const ForensicContext = createContext<ForensicContextValue | null>(null);

export function ForensicProvider({ children }: { children: React.ReactNode }) {
  const [allCases, setAllCases] = useState<InvestigationCase[]>([
    MOCK_ETH_CASE,
    MOCK_BTC_CASE,
  ]);
  const [activeCaseId, setActiveCaseId] = useState<string>(MOCK_ETH_CASE.caseId);
  const [stats, setStats] = useState<InvestigationStats>(MOCK_STATS);
  const [networkFilter, setNetworkFilter] = useState<"ALL" | BlockchainNetwork>("ALL");
  const [globalSearch, setGlobalSearch] = useState("");
  const [isOnline, setIsOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<PlatformSettings>(DEFAULT_SETTINGS);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("cryptotrace_settings");
      if (saved) {
        setSettings((prev) => ({ ...prev, ...JSON.parse(saved) }));
      }
    } catch {
      // ignore storage errors
    }
  }, []);

  const updateSettings = useCallback((patch: Partial<PlatformSettings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      try {
        localStorage.setItem("cryptotrace_settings", JSON.stringify(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (toast: Omit<ToastItem, "id">) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      setToasts((prev) => [...prev.slice(-3), { ...toast, id }]);
      setTimeout(() => {
        dismissToast(id);
      }, 4200);
    },
    [dismissToast]
  );

  const refreshData = useCallback(async () => {
    if (settings.offlineMode) {
      setIsOnline(false);
      setAllCases([MOCK_ETH_CASE, MOCK_BTC_CASE]);
      setStats(MOCK_STATS);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [remoteStats, remoteCases] = await Promise.all([
        investigationApi.getStats(),
        investigationApi.getInvestigations(),
      ]);
      if (remoteCases && remoteCases.length > 0) {
        setAllCases(remoteCases);
        setIsOnline(true);
      } else {
        setAllCases([MOCK_ETH_CASE, MOCK_BTC_CASE]);
        setIsOnline(true);
      }
      if (remoteStats && remoteStats.totalInvestigations > 0) {
        setStats(remoteStats);
      } else {
        setStats(MOCK_STATS);
      }
    } catch {
      // Automatic offline mock fallback
      setIsOnline(false);
      setAllCases((prev) => (prev.length > 0 ? prev : [MOCK_ETH_CASE, MOCK_BTC_CASE]));
      setStats(MOCK_STATS);
    } finally {
      setIsLoading(false);
    }
  }, [settings.offlineMode]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Global Cmd+K / Ctrl+K shortcut for command palette
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const activeCase = useMemo(() => {
    return (
      allCases.find((c) => c.caseId === activeCaseId) ||
      allCases[0] ||
      MOCK_ETH_CASE
    );
  }, [allCases, activeCaseId]);

  const selectCase = useCallback((caseId: string) => {
    setActiveCaseId(caseId);
  }, []);

  const addOrActivateCase = useCallback((newCase: InvestigationCase) => {
    setAllCases((prev) => [
      newCase,
      ...prev.filter((c) => c.caseId !== newCase.caseId),
    ]);
    setActiveCaseId(newCase.caseId);
  }, []);

  const value: ForensicContextValue = {
    allCases,
    activeCase,
    stats,
    networkFilter,
    setNetworkFilter,
    globalSearch,
    setGlobalSearch,
    isOnline,
    isLoading,
    error,
    settings,
    updateSettings,
    selectCase,
    addOrActivateCase,
    refreshData,
    isCopilotOpen,
    setIsCopilotOpen,
    isCommandPaletteOpen,
    setIsCommandPaletteOpen,
    toasts,
    addToast,
    dismissToast,
  };

  return (
    <ForensicContext.Provider value={value}>{children}</ForensicContext.Provider>
  );
}

export function useForensic() {
  const ctx = useContext(ForensicContext);
  if (!ctx) {
    throw new Error("useForensic must be used inside ForensicProvider");
  }
  return ctx;
}
