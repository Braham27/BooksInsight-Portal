"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Check, AlertCircle } from "lucide-react";
import { useUploadDocument, useDocuments, useExtractDocuments } from "@/hooks/use-api";
import { Button, Badge, Spinner } from "@/components/ui/primitives";
import type { DocumentResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

export function UploadZone({ caseId }: { caseId: string }) {
  const upload = useUploadDocument(caseId);

  const onDrop = useCallback(
    (files: File[]) => {
      files.forEach((file) => upload.mutate(file));
    },
    [upload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    maxSize: 10 * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
        isDragActive
          ? "border-brand-400 bg-brand-50"
          : "border-gray-300 hover:border-brand-300 hover:bg-gray-50"
      )}
    >
      <input {...getInputProps()} />
      <Upload className="mb-3 h-10 w-10 text-gray-400" />
      <p className="text-sm font-medium text-gray-700">
        {isDragActive ? "Drop files here" : "Drag & drop your W-2 or tax documents"}
      </p>
      <p className="mt-1 text-xs text-gray-500">PDF, PNG, or JPG up to 10MB</p>
      {upload.isPending && (
        <div className="mt-3 flex items-center gap-2">
          <Spinner />
          <span className="text-sm text-gray-500">Uploading document...</span>
        </div>
      )}
    </div>
  );
}

export function DocumentList({ caseId }: { caseId: string }) {
  const { data: docs, isLoading } = useDocuments(caseId);
  const extract = useExtractDocuments(caseId);

  if (isLoading) return (
    <div className="flex items-center gap-2 py-4">
      <Spinner />
      <span className="text-sm text-gray-500">Loading documents...</span>
    </div>
  );
  if (!docs?.length) return <p className="text-sm text-gray-500">No documents uploaded yet.</p>;

  const hasUploaded = docs.some((d) => d.status === "uploaded");

  return (
    <div className="space-y-3">
      {docs.map((doc) => (
        <DocumentCard key={doc.id} doc={doc} />
      ))}
      {hasUploaded && (
        <Button
          onClick={() => extract.mutate()}
          disabled={extract.isPending}
        >
          {extract.isPending ? (
            <>
              <Spinner className="mr-2 h-4 w-4" /> Extracting...
            </>
          ) : (
            "Extract All Documents"
          )}
        </Button>
      )}
    </div>
  );
}

function DocumentCard({ doc }: { doc: DocumentResponse }) {
  const statusConfig: Record<
    string,
    { variant: "default" | "success" | "warning" | "error" | "info"; icon: typeof Check }
  > = {
    uploaded: { variant: "info", icon: FileText },
    processing: { variant: "warning", icon: FileText },
    extracted: { variant: "success", icon: Check },
    verified: { variant: "success", icon: Check },
    error: { variant: "error", icon: AlertCircle },
  };

  const cfg = statusConfig[doc.status] || statusConfig.uploaded;

  return (
    <div className="flex items-center justify-between rounded-md border p-3">
      <div className="flex items-center gap-3">
        <cfg.icon className="h-5 w-5 text-gray-400" />
        <div>
          <p className="text-sm font-medium text-gray-900">{doc.file_name}</p>
          <p className="text-xs text-gray-500">
            {(doc.file_size / 1024).toFixed(0)} KB
            {doc.confidence != null && ` · ${(doc.confidence * 100).toFixed(0)}% confidence`}
          </p>
        </div>
      </div>
      <Badge variant={cfg.variant}>{doc.status}</Badge>
    </div>
  );
}

export function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (confidence == null) return null;
  const pct = confidence * 100;
  const variant = pct >= 90 ? "success" : pct >= 70 ? "warning" : "error";
  return <Badge variant={variant}>{pct.toFixed(0)}%</Badge>;
}
