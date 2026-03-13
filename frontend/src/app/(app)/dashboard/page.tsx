"use client";

import { useRouter } from "next/navigation";
import { useCases, useCreateCase } from "@/hooks/use-api";
import { Header } from "@/components/layout/sidebar";
import {
  Button,
  Card,
  CardContent,
  Badge,
  Spinner,
} from "@/components/ui/primitives";
import { Plus, FileText } from "lucide-react";
import Link from "next/link";
import type { CaseStatus } from "@/lib/types";

const STATUS_BADGE: Record<CaseStatus, "default" | "info" | "warning" | "success"> = {
  intake: "info",
  extracting: "info",
  validating: "warning",
  computing: "warning",
  review: "warning",
  complete: "success",
};

export default function DashboardPage() {
  const router = useRouter();
  const { data: cases, isLoading } = useCases();
  const createCase = useCreateCase();

  const handleNewCase = () => {
    createCase.mutate(
      {},
      {
        onSuccess: (newCase) => {
          router.push(`/cases/${newCase.id}`);
        },
      }
    );
  };

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Your Tax Cases</h2>
          <Button
            onClick={handleNewCase}
            disabled={createCase.isPending}
          >
            {createCase.isPending ? (
              <Spinner className="mr-2 h-4 w-4" />
            ) : (
              <Plus className="mr-2 h-4 w-4" />
            )}
            {createCase.isPending ? "Creating..." : "New Tax Return"}
          </Button>
        </div>

        {createCase.isError && (
          <div className="rounded-md border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">
              Failed to create tax return. Please try again.
            </p>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <Spinner className="h-8 w-8" />
              <p className="text-sm text-gray-500">Loading your tax cases...</p>
            </div>
          </div>
        )}

        {cases && cases.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <FileText className="mb-4 h-12 w-12 text-gray-300" />
              <p className="text-gray-500">
                No tax cases yet. Start a new return to begin.
              </p>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {cases?.map((c) => (
            <Link key={c.id} href={`/cases/${c.id}`}>
              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">
                      Tax Year {c.tax_year}
                    </span>
                    <Badge variant={STATUS_BADGE[c.status]}>{c.status}</Badge>
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    Created {new Date(c.created_at).toLocaleDateString()}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
