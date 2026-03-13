import { create } from "zustand";
import type { CaseResponse, CaseStatus } from "@/lib/types";

interface CaseState {
  currentCase: CaseResponse | null;
  cases: CaseResponse[];
  setCurrentCase: (c: CaseResponse | null) => void;
  setCases: (cases: CaseResponse[]) => void;
  updateCaseStatus: (caseId: string, status: CaseStatus) => void;
}

export const useCaseStore = create<CaseState>((set) => ({
  currentCase: null,
  cases: [],
  setCurrentCase: (c) => set({ currentCase: c }),
  setCases: (cases) => set({ cases }),
  updateCaseStatus: (caseId, status) =>
    set((state) => ({
      cases: state.cases.map((c) =>
        c.id === caseId ? { ...c, status } : c
      ),
      currentCase:
        state.currentCase?.id === caseId
          ? { ...state.currentCase, status }
          : state.currentCase,
    })),
}));
