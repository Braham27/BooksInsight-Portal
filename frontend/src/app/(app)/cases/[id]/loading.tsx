import { Spinner } from "@/components/ui/primitives";

export default function CaseLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <Spinner className="h-8 w-8" />
        <p className="text-sm text-gray-500">Loading tax case...</p>
      </div>
    </div>
  );
}
