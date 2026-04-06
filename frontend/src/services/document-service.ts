import { openai, OPENAI_VISION_MODEL } from "@/lib/openai";

const W2_EXTRACTION_SCHEMA = {
  type: "object" as const,
  properties: {
    doc_type: {
      type: "string",
      enum: ["W2", "1099_INT", "1099_DIV", "1099_B", "OTHER"],
      description: "The type of tax document detected",
    },
    fields: {
      type: "object",
      properties: {
        employer_name: { type: "string" },
        employer_ein: { type: "string" },
        employee_name: { type: "string" },
        ssn_last4: { type: "string", description: "Last 4 digits of SSN only." },
        wages_box1: { type: "number", description: "Box 1: Wages, tips, other compensation" },
        fed_withheld_box2: { type: "number", description: "Box 2: Federal income tax withheld" },
        ss_wages_box3: { type: "number", description: "Box 3: Social security wages" },
        ss_tax_box4: { type: "number", description: "Box 4: Social security tax withheld" },
        medicare_wages_box5: { type: "number", description: "Box 5: Medicare wages and tips" },
        medicare_tax_box6: { type: "number", description: "Box 6: Medicare tax withheld" },
        state: { type: "string", description: "Box 15: State" },
        state_wages: { type: "number", description: "Box 16: State wages" },
        state_tax_withheld: { type: "number", description: "Box 17: State income tax" },
      },
    },
    confidence: {
      type: "object",
      description: "Confidence score (0.0 to 1.0) for each extracted field",
      additionalProperties: { type: "number" },
    },
  },
  required: ["doc_type", "fields", "confidence"],
};

const EXTRACTION_SYSTEM_PROMPT = `You are a tax document extraction agent. Your job is to extract structured data from tax documents (W-2, 1099, etc.).

Rules:
1. Extract ONLY the data visible in the document.
2. Do NOT compute, interpret, or infer any tax implications.
3. For SSN, extract ONLY the last 4 digits. Never include the full SSN.
4. Provide a confidence score (0.0 to 1.0) for each extracted field.
5. If a field is not visible or unreadable, omit it and set confidence to 0.
6. Classify the document type (W2, 1099_INT, 1099_DIV, 1099_B, OTHER).
7. All monetary values should be numbers (not strings).

Return valid JSON matching the schema provided.`;

export interface ExtractionResult {
  doc_type: string;
  fields: Record<string, unknown>;
  confidence: Record<string, number>;
  warnings: string[];
}

export async function extractFromImage(
  imageBase64: string,
  mimeType: string
): Promise<ExtractionResult> {
  const response = await openai.chat.completions.create({
    model: OPENAI_VISION_MODEL,
    messages: [
      { role: "system", content: EXTRACTION_SYSTEM_PROMPT },
      {
        role: "user",
        content: [
          {
            type: "text",
            text: "Extract all fields from this tax document. Return JSON matching the extraction schema. Remember: only last 4 digits of SSN.",
          },
          {
            type: "image_url",
            image_url: {
              url: `data:${mimeType};base64,${imageBase64}`,
              detail: "high",
            },
          },
        ],
      },
    ],
    response_format: { type: "json_object" },
    max_tokens: 2000,
    temperature: 0,
  });

  const resultText = response.choices[0].message.content ?? "{}";
  const result = JSON.parse(resultText);

  // Build warnings for low-confidence fields
  const warnings: string[] = [];
  for (const [fieldName, score] of Object.entries(result.confidence ?? {})) {
    if (typeof score === "number" && score < 0.8) {
      warnings.push(`Low confidence (${Math.round(score * 100)}%) on field '${fieldName}'`);
    }
  }

  return {
    doc_type: result.doc_type ?? "OTHER",
    fields: result.fields ?? {},
    confidence: result.confidence ?? {},
    warnings,
  };
}
