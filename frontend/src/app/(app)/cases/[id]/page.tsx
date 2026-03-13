"use client";

import { useParams } from "next/navigation";
import { useCase, useNormalize, useValidate, useCompute } from "@/hooks/use-api";
import { Header } from "@/components/layout/sidebar";
import { ProgressBar } from "@/components/case/progress-bar";
import { UploadZone, DocumentList } from "@/components/case/documents";
import { ChatPanel } from "@/components/case/chat-panel";
import { TaxSummary } from "@/components/case/tax-summary";
import { ReviewPanel } from "@/components/case/review-panel";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Spinner,
  Badge,
} from "@/components/ui/primitives";

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: caseData, isLoading } = useCase(id);
  const normalize = useNormalize(id);
  const validate = useValidate(id);
  const compute = useCompute(id);

  if (isLoading || !caseData) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Spinner className="h-8 w-8" />
          <p className="text-sm text-gray-500">Loading tax case details...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Header title={`Tax Year ${caseData.tax_year}`} />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <ProgressBar status={caseData.status} />
          <Badge variant="info">{caseData.status}</Badge>
        </div>

        {/* Intake Phase: Upload + Chat */}
        {(caseData.status === "intake" || caseData.status === "extracting") && (
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Documents</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <UploadZone caseId={id} />
                <DocumentList caseId={id} />
              </CardContent>
            </Card>
            <Card className="flex flex-col" style={{ minHeight: "500px" }}>
              <CardHeader>
                <CardTitle>Tax Interview</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 p-0">
                <ChatPanel caseId={id} />
              </CardContent>
            </Card>
          </div>
        )}

        {/* Action buttons between phases */}
        {caseData.status === "intake" && (
          <div className="flex gap-3">
            <Button
              onClick={() => normalize.mutate()}
              disabled={normalize.isPending}
            >
              {normalize.isPending ? <Spinner className="mr-2 h-4 w-4" /> : null}
              Finalize Intake & Validate
            </Button>
          </div>
        )}

        {caseData.status === "validating" && (
          <Card>
            <CardHeader>
              <CardTitle>Validation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-600">
                Your tax information has been gathered. Run validation to check for
                any issues before computing your taxes.
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => validate.mutate()}
                  disabled={validate.isPending}
                >
                  {validate.isPending ? <Spinner className="mr-2 h-4 w-4" /> : null}
                  Run Validation
                </Button>
                <Button
                  variant="outline"
                  onClick={() => compute.mutate()}
                  disabled={compute.isPending}
                >
                  {compute.isPending ? <Spinner className="mr-2 h-4 w-4" /> : null}
                  Compute Taxes
                </Button>
              </div>
              {validate.data && (
                <div className="space-y-2">
                  {validate.data.errors.map((e, i) => (
                    <p key={i} className="text-sm text-red-600">
                      ✗ {e.field}: {e.message}
                    </p>
                  ))}
                  {validate.data.warnings.map((w, i) => (
                    <p key={i} className="text-sm text-yellow-600">
                      ⚠ {w.field}: {w.message}
                    </p>
                  ))}
                  {validate.data.valid && (
                    <p className="text-sm text-green-600">✓ All checks passed</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {caseData.status === "computing" && (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <Spinner className="mr-3" />
              <span className="text-gray-600">Computing your taxes...</span>
            </CardContent>
          </Card>
        )}

        {/* Review Phase: Show results + review controls */}
        {(caseData.status === "review" || caseData.status === "complete") && (
          <>
            <TaxSummary caseId={id} />
            {caseData.status === "review" && <ReviewPanel caseId={id} />}
            {caseData.status === "complete" && (
              <Card className="border-green-200 bg-green-50">
                <CardContent className="p-6 text-center">
                  <p className="text-lg font-semibold text-green-800">
                    ✓ Tax Return Finalized
                  </p>
                  <p className="text-sm text-green-600 mt-1">
                    Your return has been reviewed and approved.
                  </p>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </>
  );
}
