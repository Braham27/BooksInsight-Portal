import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  CaseResponse,
  CaseCreateRequest,
  DocumentResponse,
  ExtractionResponse,
  ChatResponse,
  ChatMessageResponse,
  ComputationResponse,
  ValidationResponse,
  CaseSummary,
  ReviewResponse,
  ReviewCreateRequest,
} from "@/lib/types";

// ---- Cases ----
export function useCases() {
  return useQuery<CaseResponse[]>({
    queryKey: ["cases"],
    queryFn: async () => {
      const { data } = await api.get("/cases");
      return data.cases;
    },
  });
}

export function useCase(caseId: string) {
  return useQuery<CaseResponse>({
    queryKey: ["case", caseId],
    queryFn: async () => {
      const { data } = await api.get(`/cases/${caseId}`);
      return data;
    },
    enabled: !!caseId,
  });
}

export function useCreateCase() {
  const qc = useQueryClient();
  return useMutation<CaseResponse, Error, CaseCreateRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post("/cases", body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cases"] }),
  });
}

// ---- Documents ----
export function useDocuments(caseId: string) {
  return useQuery<DocumentResponse[]>({
    queryKey: ["documents", caseId],
    queryFn: async () => {
      const { data } = await api.get(`/cases/${caseId}/documents`);
      return data;
    },
    enabled: !!caseId,
  });
}

export function useUploadDocument(caseId: string) {
  const qc = useQueryClient();
  return useMutation<DocumentResponse, Error, File>({
    mutationFn: async (file) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post(`/cases/${caseId}/documents`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", caseId] }),
  });
}

// ---- Extraction ----
export function useExtractDocuments(caseId: string) {
  const qc = useQueryClient();
  return useMutation<ExtractionResponse[], Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/cases/${caseId}/extract`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", caseId] }),
  });
}

// ---- Chat ----
export function useChatHistory(caseId: string) {
  return useQuery<ChatMessageResponse[]>({
    queryKey: ["chat", caseId],
    queryFn: async () => {
      const { data } = await api.get(`/cases/${caseId}/chat/history`);
      return data;
    },
    enabled: !!caseId,
  });
}

export function useSendMessage(caseId: string) {
  const qc = useQueryClient();
  return useMutation<ChatResponse, Error, string>({
    mutationFn: async (message) => {
      const { data } = await api.post(`/cases/${caseId}/chat`, { message });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chat", caseId] }),
  });
}

// ---- Intake ----
export function useNormalize(caseId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/cases/${caseId}/normalize`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["case", caseId] }),
  });
}

// ---- Validation ----
export function useValidate(caseId: string) {
  return useMutation<ValidationResponse, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/cases/${caseId}/validate`);
      return data;
    },
  });
}

// ---- Computation ----
export function useCompute(caseId: string) {
  const qc = useQueryClient();
  return useMutation<ComputationResponse, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/cases/${caseId}/compute`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["case", caseId] }),
  });
}

export function useComputation(caseId: string) {
  return useQuery<ComputationResponse>({
    queryKey: ["computation", caseId],
    queryFn: async () => {
      const { data } = await api.get(`/cases/${caseId}/computation`);
      return data;
    },
    enabled: !!caseId,
  });
}

// ---- Review ----
export function useSubmitReview(caseId: string) {
  const qc = useQueryClient();
  return useMutation<ReviewResponse, Error, ReviewCreateRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post(`/cases/${caseId}/review`, body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["case", caseId] }),
  });
}

// ---- Summary ----
export function useCaseSummary(caseId: string) {
  return useQuery<CaseSummary>({
    queryKey: ["summary", caseId],
    queryFn: async () => {
      const { data } = await api.get(`/cases/${caseId}/summary`);
      return data;
    },
    enabled: !!caseId,
  });
}
