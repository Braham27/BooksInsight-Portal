"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center space-y-4">
            <h2 className="text-2xl font-bold">Something went wrong</h2>
            <p className="text-gray-600">{error.message}</p>
            <button
              onClick={reset}
              className="rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
