import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { logAuditEvent } from "@/services/audit-service";
import { toSnakeCase } from "@/lib/serialize";

// POST /api/cases — create a new case
export async function POST(request: NextRequest) {
  const user = await getAuthUser();
  const body = await request.json().catch(() => ({}));
  const taxYear = body.tax_year ?? 2025;

  const newCase = await prisma.case.create({
    data: {
      userId: user.userId,
      taxYear,
      status: "intake",
    },
  });

  await logAuditEvent({
    userId: user.userId,
    action: "case_created",
    entityType: "case",
    entityId: newCase.id,
    caseId: newCase.id,
    newValue: { tax_year: taxYear },
  });

  return NextResponse.json(toSnakeCase(newCase), { status: 201 });
}

// GET /api/cases — list user's cases
export async function GET() {
  const user = await getAuthUser();

  const cases = await prisma.case.findMany({
    where: { userId: user.userId },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json({ cases: cases.map(c => toSnakeCase(c)), total: cases.length });
}
