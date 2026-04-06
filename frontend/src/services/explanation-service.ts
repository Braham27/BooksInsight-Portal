import { openai, OPENAI_MODEL } from "@/lib/openai";

export async function generateExplanation(
  computeResult: Record<string, unknown>,
  factsData: Record<string, unknown>
): Promise<string> {
  const response = await openai.chat.completions.create({
    model: OPENAI_MODEL,
    messages: [
      {
        role: "system",
        content: `You are a tax explanation assistant. Your job is to explain tax computation results in plain, friendly language.

Rules:
1. Reference the actual numbers from the computation.
2. Explain what each major line item means.
3. Do NOT recompute or verify the numbers — the engine is the source of truth.
4. Keep explanations concise (3-5 paragraphs).
5. Mention the filing status and tax year.
6. If there's a refund, explain why. If there's an amount owed, explain why.
7. Do not give tax advice — just explain the numbers.`,
      },
      {
        role: "user",
        content: `Here are the tax computation results to explain:\n\n${JSON.stringify(computeResult, null, 2)}\n\nTax facts used:\n${JSON.stringify(factsData, null, 2)}`,
      },
    ],
    temperature: 0.5,
    max_tokens: 1000,
  });

  return response.choices[0].message.content ?? "Unable to generate explanation.";
}
