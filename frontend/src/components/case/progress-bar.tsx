"use client";

import { CaseStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS: { key: CaseStatus; label: string }[] = [
  { key: "intake", label: "Intake" },
  { key: "extracting", label: "Documents" },
  { key: "validating", label: "Validate" },
  { key: "computing", label: "Compute" },
  { key: "review", label: "Review" },
  { key: "complete", label: "Complete" },
];

const ORDER: Record<CaseStatus, number> = {
  intake: 0,
  extracting: 1,
  validating: 2,
  computing: 3,
  review: 4,
  complete: 5,
};

export function ProgressBar({ status }: { status: CaseStatus }) {
  const current = ORDER[status];

  return (
    <div className="flex items-center gap-1">
      {STEPS.map((step, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={step.key} className="flex items-center gap-1">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium",
                  done && "bg-green-500 text-white",
                  active && "bg-brand-600 text-white",
                  !done && !active && "bg-gray-200 text-gray-500"
                )}
              >
                {done ? "✓" : i + 1}
              </div>
              <span className="mt-1 text-xs text-gray-600">{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "mb-5 h-0.5 w-8",
                  i < current ? "bg-green-500" : "bg-gray-200"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
