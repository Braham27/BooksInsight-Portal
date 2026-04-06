import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { normalizeFacts } from "@/services/interview-service";

// POST /api/cases/[caseId]/normalize — normalize extracted facts
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

  const result = await normalizeFacts(caseId);

  await prisma.case.update({
    where: { id: caseId },
    data: { status: "validating" },
  });

  return NextResponse.json(result);
}
