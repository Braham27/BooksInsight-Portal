import { NextRequest, NextResponse } from "next/server";
import { prisma, Prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { extractFromImage } from "@/services/document-service";
import { readFile } from "fs/promises";
import path from "path";

// POST /api/cases/[caseId]/extract — extract data from all uploaded docs
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

  // Update case status
  await prisma.case.update({
    where: { id: caseId },
    data: { status: "extracting" },
  });

  const docs = await prisma.document.findMany({
    where: { caseId, status: "uploaded" },
  });

  if (docs.length === 0) {
    return NextResponse.json(
      { error: "No documents awaiting extraction" },
      { status: 400 }
    );
  }

  const results = [];

  for (const doc of docs) {
    try {
      // Mark processing
      await prisma.document.update({
        where: { id: doc.id },
        data: { status: "processing" },
      });

      // Read file from disk
      const fullPath = path.join(process.cwd(), doc.filePath);
      const buffer = await readFile(fullPath);
      const base64 = buffer.toString("base64");

      const extraction = await extractFromImage(base64, doc.mimeType);

      // Update document with extraction results
      await prisma.document.update({
        where: { id: doc.id },
        data: {
          status: "extracted",
          docType: extraction.doc_type?.toLowerCase() ?? null,
          extractedData: (extraction.fields ?? {}) as Prisma.InputJsonValue,
          evidence: (extraction.confidence ?? {}) as Prisma.InputJsonValue,
          confidence: Object.values(extraction.confidence ?? {}).reduce((a, b) => a + b, 0) / Math.max(Object.keys(extraction.confidence ?? {}).length, 1),
        },
      });

      results.push({
        document_id: doc.id,
        doc_type: extraction.doc_type?.toLowerCase() ?? null,
        extracted_data: extraction.fields ?? {},
        confidence: Object.values(extraction.confidence ?? {}).reduce((a, b) => a + b, 0) / Math.max(Object.keys(extraction.confidence ?? {}).length, 1),
        status: "extracted",
      });
    } catch (err) {
      await prisma.document.update({
        where: { id: doc.id },
        data: { status: "error" },
      });
      results.push({
        document_id: doc.id,
        doc_type: null,
        extracted_data: {},
        confidence: 0,
        status: "error",
      });
    }
  }

  return NextResponse.json(results);
}
