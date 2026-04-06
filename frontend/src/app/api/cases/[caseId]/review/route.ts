import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { logAuditEvent } from "@/services/audit-service";
import { toSnakeCase } from "@/lib/serialize";

// POST /api/cases/[caseId]/review — submit a review
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  const { caseId } = await params;
  const user = await getAuthUser();

  const caseData = await prisma.case.findUnique({ where: { id: caseId } });
  if (!caseData) {
    return NextResponse.json({ error: "Case not found" }, { status: 404 });
  }
  if (caseData.userId !== user.userId && user.role !== "admin") {
    return NextResponse.json({ error: "Access denied" }, { status: 403 });
  }
  if (caseData.status !== "review") {
    return NextResponse.json(
      { error: "Case is not in review status" },
      { status: 400 }
    );
  }

  const body = await request.json();
  const { decision, notes } = body;

  if (!decision || !["approved", "rejected", "needs_changes"].includes(decision)) {
    return NextResponse.json(
      { error: "Invalid decision" },
      { status: 400 }
    );
  }

  const review = await prisma.review.create({
    data: {
      caseId,
      reviewerId: user.userId,
      decision,
      notes: notes ?? null,
    },
  });

  if (decision === "approved") {
    await prisma.case.update({
      where: { id: caseId },
      data: { status: "complete" },
    });
  }

  await logAuditEvent({
    userId: user.userId,
    action: "review_submitted",
    entityType: "review",
    entityId: review.id,
    caseId,
    newValue: { decision, notes },
  });

  return NextResponse.json(toSnakeCase(review), { status: 201 });
}
