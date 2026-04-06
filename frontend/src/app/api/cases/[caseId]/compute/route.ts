import { NextRequest, NextResponse } from "next/server";
import { prisma, Prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { computeTaxes } from "@/services/tax-engine";
import { generateExplanation } from "@/services/explanation-service";
import { logAuditEvent } from "@/services/audit-service";

// POST /api/cases/[caseId]/compute — run tax computation
export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  const { caseId } = await params;
  const user = await getAuthUser();

  const caseData = await prisma.case.findUnique({ where: { id: caseId } });
  if (!caseData) {
    return NextResponse.json({ error: "Case not found" }, { status: 404 });
  }
  if (caseData.userId !== user.userId) {
    return NextResponse.json({ error: "Access denied" }, { status: 403 });
  }

  // Get latest tax facts
  const facts = await prisma.taxFact.findFirst({
    where: { caseId },
    orderBy: { version: "desc" },
  });

  if (!facts) {
    return NextResponse.json(
      { error: "No tax facts available. Complete intake first." },
      { status: 400 }
    );
  }

  // Update status
  await prisma.case.update({
    where: { id: caseId },
    data: { status: "computing" },
  });

  const factsData = facts.factsData as Record<string, unknown>;
  const compResult = computeTaxes(factsData, caseData.taxYear);
  const explanation = await generateExplanation(
    compResult as unknown as Record<string, unknown>,
    factsData
  );

  // Save computation
  const computation = await prisma.computation.create({
    data: {
      caseId,
      engineName: compResult.engine_name ?? "booksinsight-ts",
      engineVersion: compResult.engine_version ?? "0.1.0",
      inputPayload: factsData as Prisma.InputJsonValue,
      outputPayload: compResult as unknown as Prisma.InputJsonValue,
      explanation,
    },
  });

  // Move to review
  await prisma.case.update({
    where: { id: caseId },
    data: { status: "review" },
  });

  await logAuditEvent({
    userId: user.userId,
    action: "computation_completed",
    entityType: "computation",
    entityId: computation.id,
    caseId,
    newValue: {
      engine: computation.engineName,
      refund_or_balance: compResult.refund_or_balance,
    },
  });

  return NextResponse.json({
    id: computation.id,
    case_id: caseId,
    engine_name: computation.engineName,
    engine_version: computation.engineVersion,
    result: compResult,
    explanation,
    created_at: computation.createdAt.toISOString(),
  });
}
