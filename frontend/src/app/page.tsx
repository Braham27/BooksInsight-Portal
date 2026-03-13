import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";

export default async function HomePage() {
  const { userId } = await auth();
  if (userId) {
    redirect("/dashboard");
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-brand-50 to-white">
      <div className="text-center space-y-6 max-w-2xl px-4">
        <h1 className="text-5xl font-bold text-gray-900">
          AI-Assisted Tax Preparation
        </h1>
        <p className="text-xl text-gray-600">
          Upload your W-2, answer a few questions, and get your federal tax
          return computed — with plain-language explanations at every step.
        </p>
        <div className="flex gap-4 justify-center">
          <a
            href="/sign-in"
            className="inline-flex items-center justify-center rounded-md bg-brand-600 px-6 py-3 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
          >
            Sign In
          </a>
          <a
            href="/sign-up"
            className="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-6 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Create Account
          </a>
        </div>
      </div>
    </div>
  );
}
