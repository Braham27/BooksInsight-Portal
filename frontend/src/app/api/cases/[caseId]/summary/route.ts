import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";

// GET /api/cases/[caseId]/summary — full case summary
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

  const [docs, facts, computation, reviews] = await Promise.all([
    prisma.document.findMany({ where: { caseId } }),
    prisma.taxFact.findFirst({
      where: { caseId },
      orderBy: { version: "desc" },
    }),
    prisma.computation.findFirst({
      where: { caseId },
      orderBy: { createdAt: "desc" },
    }),
    prisma.review.findMany({
      where: { caseId },
      orderBy: { createdAt: "desc" },
    }),
  ]);

  return NextResponse.json({
    case: {
      id: caseData.id,
      tax_year: caseData.taxYear,
      status: caseData.status,
      filing_status: caseData.filingStatus,
      created_at: caseData.createdAt?.toISOString() ?? null,
    },
    documents: docs.map((d) => ({
      id: d.id,
      file_name: d.fileName,
      doc_type: d.docType,
      status: d.status,
    })),
    tax_facts: facts ? (facts.factsData as Record<string, unknown>) : null,
    computation: computation
      ? {
          engine: computation.engineName,
          result: computation.outputPayload,
          explanation: computation.explanation,
        }
      : null,
    reviews: reviews.map((r) => ({
      id: r.id,
      decision: r.decision,
      notes: r.notes,
      created_at: r.createdAt.toISOString(),
    })),
  });
}
