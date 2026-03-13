"use client";

import { useState } from "react";
import { useSubmitReview } from "@/hooks/use-api";
import { Button, Card, CardContent, CardHeader, CardTitle, Textarea, Spinner } from "@/components/ui/primitives";
import type { ReviewDecision } from "@/lib/types";

export function ReviewPanel({ caseId }: { caseId: string }) {
  const [notes, setNotes] = useState("");
  const submit = useSubmitReview(caseId);

  const handleSubmit = (decision: ReviewDecision) => {
    submit.mutate({ decision, notes: notes || undefined });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review & Approve</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-600">
          Review the tax computation results above. If everything looks correct,
          approve to finalize. If changes are needed, reject with notes explaining
          what needs correction.
        </p>
        <Textarea
          placeholder="Optional notes..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <div className="flex gap-3">
          <Button
            onClick={() => handleSubmit("approved")}
            disabled={submit.isPending}
          >
            {submit.isPending ? <Spinner className="mr-2 h-4 w-4" /> : null}
            Approve & Finalize
          </Button>
          <Button
            variant="outline"
            onClick={() => handleSubmit("needs_changes")}
            disabled={submit.isPending}
          >
            Request Changes
          </Button>
          <Button
            variant="destructive"
            onClick={() => handleSubmit("rejected")}
            disabled={submit.isPending}
          >
            Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
