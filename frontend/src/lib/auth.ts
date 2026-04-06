import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

export interface AuthUser {
  userId: string;
  role: string;
}

/**
 * Get the authenticated user from Clerk. Throws a NextResponse 401 if unauthenticated.
 */
export async function getAuthUser(): Promise<AuthUser> {
  const { userId, sessionClaims } = await auth();

  if (!userId) {
    throw NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const role = (sessionClaims?.metadata as { role?: string })?.role ?? "user";

  return { userId, role };
}
