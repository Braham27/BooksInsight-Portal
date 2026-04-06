import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { validateTaxFacts } from "@/services/validation-service";

// POST /api/cases/[caseId]/validate — validate tax facts
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
  if (caseData.userId !== user.userId && user.role !== "admin") {
    return NextResponse.json({ error: "Access denied" }, { status: 403 });
  }

  // Get latest tax facts
  const facts = await prisma.taxFact.findFirst({
    where: { caseId },
    orderBy: { version: "desc" },
  });

  if (!facts) {
    return NextResponse.json(
      { error: "No tax facts to validate. Run normalize first." },
      { status: 400 }
    );
  }

  const validation = validateTaxFacts(
    facts.factsData as Record<string, unknown>
  );
  return NextResponse.json(validation);
}
