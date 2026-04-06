import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";

// GET /api/cases/[caseId]/computation — get latest computation
export async function GET(
  _request: NextRequest,
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

  const comp = await prisma.computation.findFirst({
    where: { caseId },
    orderBy: { createdAt: "desc" },
  });

  if (!comp) {
    return NextResponse.json(
      { error: "No computation found" },
      { status: 404 }
    );
  }

  return NextResponse.json({
    id: comp.id,
    case_id: caseId,
    engine_name: comp.engineName,
    engine_version: comp.engineVersion,
    result: comp.outputPayload,
    explanation: comp.explanation,
    created_at: comp.createdAt.toISOString(),
  });
}
