import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold">Page Not Found</h2>
        <p className="text-gray-600">Could not find the requested page.</p>
        <Link
          href="/"
          className="inline-block rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700"
        >
          Go Home
        </Link>
      </div>
    </div>
  );
}
