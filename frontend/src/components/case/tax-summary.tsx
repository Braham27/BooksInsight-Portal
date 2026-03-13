"use client";

import { useComputation } from "@/hooks/use-api";
import { Card, CardContent, CardHeader, CardTitle, Badge, Spinner } from "@/components/ui/primitives";
import type { ComputationResponse } from "@/lib/types";
import { DollarSign, TrendingDown, TrendingUp } from "lucide-react";

export function TaxSummary({ caseId }: { caseId: string }) {
  const { data, isLoading } = useComputation(caseId);

  if (isLoading) return (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center gap-3">
        <Spinner className="h-8 w-8" />
        <p className="text-sm text-gray-500">Calculating your tax summary...</p>
      </div>
    </div>
  );
  if (!data) return null;

  return (
    <div className="space-y-6">
      <RefundBanner result={data} />
      <LineItemTable result={data} />
      {data.explanation && (
        <Card>
          <CardHeader>
            <CardTitle>Plain-Language Explanation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm text-gray-700">
              {data.explanation}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RefundBanner({ result }: { result: ComputationResponse }) {
  const amount = result.result.refund_or_balance;
  const isRefund = amount > 0;

  return (
    <Card
      className={
        isRefund
          ? "border-green-200 bg-green-50"
          : "border-red-200 bg-red-50"
      }
    >
      <CardContent className="flex items-center gap-4 p-6">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-full ${
            isRefund ? "bg-green-100" : "bg-red-100"
          }`}
        >
          {isRefund ? (
            <TrendingUp className="h-6 w-6 text-green-600" />
          ) : (
            <TrendingDown className="h-6 w-6 text-red-600" />
          )}
        </div>
        <div>
          <p className="text-sm font-medium text-gray-600">
            {isRefund ? "Estimated Refund" : "Estimated Amount Owed"}
          </p>
          <p
            className={`text-3xl font-bold ${
              isRefund ? "text-green-700" : "text-red-700"
            }`}
          >
            ${Math.abs(amount).toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </p>
        </div>
        <Badge variant="info" className="ml-auto">
          {result.engine_name} v{result.engine_version}
        </Badge>
      </CardContent>
    </Card>
  );
}

function LineItemTable({ result }: { result: ComputationResponse }) {
  const items = result.result.line_items || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tax Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="pb-2">Item</th>
              <th className="pb-2 text-right">Amount</th>
              <th className="pb-2 text-right">Form Line</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr key={i} className="border-b last:border-0">
                <td className="py-2 text-gray-900">{item.label}</td>
                <td className="py-2 text-right font-mono">
                  ${item.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </td>
                <td className="py-2 text-right text-gray-500">
                  {item.form_line || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
