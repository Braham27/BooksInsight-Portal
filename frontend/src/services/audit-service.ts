import { prisma, Prisma } from "@/lib/db";

interface AuditEventParams {
  userId: string;
  action: string;
  entityType: string;
  entityId?: string;
  caseId?: string;
  oldValue?: Record<string, unknown>;
  newValue?: Record<string, unknown>;
  ipAddress?: string;
}

export async function logAuditEvent(params: AuditEventParams) {
  await prisma.auditLog.create({
    data: {
      userId: params.userId,
      action: params.action,
      entityType: params.entityType,
      entityId: params.entityId ?? null,
      caseId: params.caseId ?? null,
      oldValue: (params.oldValue ?? undefined) as Prisma.InputJsonValue | undefined,
      newValue: (params.newValue ?? undefined) as Prisma.InputJsonValue | undefined,
      ipAddress: params.ipAddress ?? null,
    },
  });
}
