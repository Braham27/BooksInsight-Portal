import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getAuthUser } from "@/lib/auth";
import { logAuditEvent } from "@/services/audit-service";
import { toSnakeCase } from "@/lib/serialize";
import { randomUUID } from "crypto";

const ALLOWED_MIME_TYPES = new Set([
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/gif",
  "application/pdf",
]);

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

// POST /api/cases/[caseId]/documents — upload a document
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

  const formData = await request.formData();
  const file = formData.get("file") as File | null;
  if (!file) {
    return NextResponse.json({ error: "No file provided" }, { status: 400 });
  }

  if (!ALLOWED_MIME_TYPES.has(file.type)) {
    return NextResponse.json(
      { error: `Unsupported file type: ${file.type}` },
      { status: 400 }
    );
  }

  const buffer = Buffer.from(await file.arrayBuffer());
  if (buffer.length > MAX_FILE_SIZE) {
    return NextResponse.json(
      { error: "File exceeds 10 MB limit" },
      { status: 400 }
    );
  }

  // Store file content as base64 in database (Vercel has read-only filesystem)
  const base64Content = buffer.toString("base64");
  const safeFilename = `${randomUUID()}${file.name.substring(file.name.lastIndexOf("."))}`;

  const doc = await prisma.document.create({
    data: {
      caseId,
      filePath: `uploads/${caseId}/${safeFilename}`,
      fileName: file.name,
      fileSize: buffer.length,
      mimeType: file.type,
      fileContent: base64Content,
      status: "uploaded",
    },
  });

  await logAuditEvent({
    userId: user.userId,
    action: "document_uploaded",
    entityType: "document",
    entityId: doc.id,
    caseId,
    newValue: {
      file_name: doc.fileName,
      mime_type: doc.mimeType,
      size: doc.fileSize,
    },
  });

  return NextResponse.json(toSnakeCase(doc), { status: 201 });
}

// GET /api/cases/[caseId]/documents — list documents
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

  const docs = await prisma.document.findMany({
    where: { caseId },
    orderBy: { createdAt: "asc" },
  });

  return NextResponse.json(docs.map(d => toSnakeCase(d)));
}
