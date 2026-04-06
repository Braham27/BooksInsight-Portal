import { prisma, Prisma } from "@/lib/db";
import { openai, OPENAI_MODEL } from "@/lib/openai";

// Interview steps and the facts each step needs
const INTERVIEW_STEPS = [
  { name: "greeting", description: "Greet the user and ask them to upload documents or start answering questions", required_facts: [] as string[] },
  { name: "filing_status", description: "Determine filing status", required_facts: ["filing_status"] },
  { name: "taxpayer_info", description: "Collect taxpayer name and basic info", required_facts: ["primary_taxpayer.first_name", "primary_taxpayer.last_name"] },
  { name: "income_review", description: "Review W-2 income and ask about additional income sources", required_facts: ["income.w2"] },
  { name: "dependents", description: "Ask about dependents", required_facts: ["dependents_asked"] },
  { name: "deductions", description: "Confirm standard deduction (MVP only supports standard)", required_facts: ["deduction_confirmed"] },
  { name: "missing_docs", description: "Check for any missing documents", required_facts: ["docs_complete"] },
  { name: "complete", description: "Interview is complete, ready for computation", required_facts: [] as string[] },
];

const STEP_INSTRUCTIONS: Record<string, string> = {
  greeting: "Welcome the user warmly. Tell them you can help with their US federal taxes. Ask if they have their W-2 ready to upload, or if they'd prefer to answer questions first.",
  filing_status: "Ask about their filing status. Explain the options in plain language: Single, Married Filing Jointly (MFJ), Married Filing Separately (MFS), Head of Household (HOH), or Qualifying Surviving Spouse (QSS). Extract the chosen status.",
  taxpayer_info: "Ask for the taxpayer's name. If we already have it from a W-2, confirm it.",
  income_review: "If W-2 data exists from document upload, summarize what was found and ask the user to confirm. If no W-2 uploaded, ask if they have W-2 income and collect the amounts. Ask if they have any other W-2s.",
  dependents: "Ask if the user has any dependents (children or qualifying relatives). Collect basic info for each: name, date of birth, relationship. If none, that's fine.",
  deductions: "For this version, we only support the standard deduction. Let the user know we'll apply the standard deduction. Ask if they're over 65 or legally blind (as these affect the standard deduction amount).",
  missing_docs: "Review what we have and ask if there's anything else. Remind them this MVP only handles W-2 income. If they mention 1099s or other income, let them know that's coming in a future version.",
  complete: "Summarize everything collected and let the user know we're ready to calculate their federal tax estimate.",
};

const INTERVIEW_SYSTEM_PROMPT = `You are a friendly tax preparation assistant for a US federal tax system.
Your role is to interview the user and collect tax information step by step.

Rules:
1. Ask ONE question at a time. Be conversational and clear.
2. NEVER compute taxes or make tax decisions.
3. NEVER "guess" missing numbers.
4. If the user's answer is ambiguous, ask clarifying questions.
5. Translate tax jargon into plain language.
6. When extracting structured data from answers, be precise.

Current interview step: {current_step}
Step description: {step_description}
Known facts so far: {known_facts}
Missing information: {missing_info}

Instructions for this step: {step_instructions}

Respond with a JSON object containing:
- "message": your conversational response to the user
- "extracted_facts": any structured data extracted from the user's answer (or null)
- "step_complete": boolean indicating if this step's required facts are now collected`;

function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");
  let current: unknown = obj;
  for (const part of parts) {
    if (current && typeof current === "object" && part in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return current;
}

function getCurrentStep(factsData: Record<string, unknown>) {
  for (const step of INTERVIEW_STEPS) {
    if (step.name === "greeting" && factsData.greeting_done) continue;
    if (step.name === "complete") return step;

    let allPresent = true;
    for (const fact of step.required_facts) {
      if (getNestedValue(factsData, fact) === undefined) {
        allPresent = false;
        break;
      }
    }
    if (!allPresent) return step;
  }
  return INTERVIEW_STEPS[INTERVIEW_STEPS.length - 1];
}

function computeProgress(factsData: Record<string, unknown>) {
  const totalSteps = INTERVIEW_STEPS.length - 1; // exclude "complete"
  const completed: string[] = [];
  const remaining: string[] = [];

  for (const step of INTERVIEW_STEPS) {
    if (step.name === "complete") continue;

    let allPresent = true;
    for (const fact of step.required_facts) {
      if (getNestedValue(factsData, fact) === undefined) {
        allPresent = false;
        break;
      }
    }

    if (allPresent && (step.required_facts.length > 0 || (step.name === "greeting" && factsData.greeting_done))) {
      completed.push(step.name);
    } else {
      remaining.push(step.name);
    }
  }

  const currentStep = getCurrentStep(factsData);
  const pct = Math.min(Math.round((completed.length / Math.max(totalSteps, 1)) * 100), 100);

  return {
    current_step: currentStep.name,
    completion_pct: pct,
    steps_completed: completed,
    steps_remaining: remaining,
  };
}

export async function processMessage(caseId: string, userMessage: string) {
  // Save user message
  await prisma.chatMessage.create({
    data: { caseId, role: "user", content: userMessage },
  });

  // Get current facts
  const latestFact = await prisma.taxFact.findFirst({
    where: { caseId },
    orderBy: { version: "desc" },
  });
  const factsData = (latestFact?.factsData as Record<string, unknown>) ?? {};

  // Get chat history
  const history = await prisma.chatMessage.findMany({
    where: { caseId },
    orderBy: { createdAt: "asc" },
    take: 20,
  });

  const currentStep = getCurrentStep(factsData);

  // Find missing info
  const missingInfo: string[] = [];
  for (const fact of currentStep.required_facts) {
    if (getNestedValue(factsData, fact) === undefined) {
      missingInfo.push(fact);
    }
  }

  // Build system prompt
  const systemPrompt = INTERVIEW_SYSTEM_PROMPT
    .replace("{current_step}", currentStep.name)
    .replace("{step_description}", currentStep.description)
    .replace("{known_facts}", factsData && Object.keys(factsData).length > 0 ? JSON.stringify(factsData, null, 2) : "None yet")
    .replace("{missing_info}", missingInfo.length > 0 ? missingInfo.join(", ") : "None")
    .replace("{step_instructions}", STEP_INSTRUCTIONS[currentStep.name] ?? "");

  // Build LLM messages
  const llmMessages: Array<{ role: "system" | "user" | "assistant"; content: string }> = [
    { role: "system", content: systemPrompt },
  ];
  for (const msg of history.slice(-10)) {
    llmMessages.push({
      role: msg.role as "user" | "assistant",
      content: msg.content,
    });
  }

  const response = await openai.chat.completions.create({
    model: OPENAI_MODEL,
    messages: llmMessages,
    response_format: { type: "json_object" },
    temperature: 0.7,
    max_tokens: 1000,
  });

  const resultText = response.choices[0].message.content ?? "{}";
  const result = JSON.parse(resultText);

  const assistantText = result.message ?? "I'm not sure how to respond to that.";
  const extractedFacts = result.extracted_facts as Record<string, unknown> | null;
  const stepComplete = result.step_complete ?? false;

  let structuredOutput: Record<string, unknown> | null = null;

  if (extractedFacts) {
    // Merge extracted facts
    const updatedFacts: Record<string, unknown> = { ...factsData };
    for (const [key, value] of Object.entries(extractedFacts)) {
      if (typeof value === "object" && value !== null && !Array.isArray(value) && key in updatedFacts && typeof updatedFacts[key] === "object") {
        updatedFacts[key] = { ...(updatedFacts[key] as Record<string, unknown>), ...(value as Record<string, unknown>) };
      } else {
        updatedFacts[key] = value;
      }
    }

    if (stepComplete && currentStep.name === "greeting") {
      updatedFacts.greeting_done = true;
    }

    const newVersion = (latestFact?.version ?? 0) + 1;
    await prisma.taxFact.create({
      data: {
        caseId,
        version: newVersion,
        factsData: updatedFacts as Prisma.InputJsonValue,
        sourceMap: { source: "interview", step: currentStep.name } as Prisma.InputJsonValue,
      },
    });

    structuredOutput = extractedFacts;

    // Update case
    const caseUpdate: Record<string, unknown> = {};
    if ("filing_status" in extractedFacts) {
      caseUpdate.filingStatus = extractedFacts.filing_status as string;
    }
    const tp = extractedFacts.primary_taxpayer as Record<string, string> | undefined;
    if (tp) {
      const parts = [tp.first_name, tp.last_name].filter(Boolean);
      if (parts.length > 0) caseUpdate.taxpayerName = parts.join(" ");
    }
    if (Object.keys(caseUpdate).length > 0) {
      await prisma.case.update({ where: { id: caseId }, data: caseUpdate });
    }
  } else if (stepComplete && currentStep.name === "greeting") {
    const updatedFacts = { ...factsData, greeting_done: true };
    const newVersion = (latestFact?.version ?? 0) + 1;
    await prisma.taxFact.create({
      data: {
        caseId,
        version: newVersion,
        factsData: updatedFacts,
        sourceMap: { source: "interview", step: "greeting" },
      },
    });
  }

  // Save assistant message
  const assistantMsg = await prisma.chatMessage.create({
    data: {
      caseId,
      role: "assistant",
      content: assistantText,
      structuredOutput: (structuredOutput ?? undefined) as Prisma.InputJsonValue | undefined,
    },
  });

  // Compute progress
  const finalFact = await prisma.taxFact.findFirst({
    where: { caseId },
    orderBy: { version: "desc" },
  });
  const finalFacts = (finalFact?.factsData as Record<string, unknown>) ?? {};
  const progress = computeProgress(finalFacts);

  return {
    assistant_message: {
      id: assistantMsg.id,
      role: assistantMsg.role,
      content: assistantMsg.content,
      structured_output: assistantMsg.structuredOutput,
      created_at: assistantMsg.createdAt.toISOString(),
    },
    structured_update: structuredOutput,
    progress,
    unresolved_questions: missingInfo,
  };
}

export async function normalizeFacts(caseId: string) {
  const caseData = await prisma.case.findUniqueOrThrow({ where: { id: caseId } });

  // Get latest interview facts
  const latestFact = await prisma.taxFact.findFirst({
    where: { caseId },
    orderBy: { version: "desc" },
  });
  const factsData = (latestFact?.factsData as Record<string, unknown>) ?? {};

  // Get extracted documents
  const documents = await prisma.document.findMany({
    where: { caseId, status: { in: ["extracted", "verified"] } },
  });

  const income = (factsData.income as Record<string, unknown>) ?? {};
  const w2List = (income.w2 as Array<Record<string, unknown>>) ?? [];
  let totalWithheld = 0;

  for (const doc of documents) {
    if (doc.docType === "W2" && doc.extractedData) {
      const data = doc.extractedData as Record<string, unknown>;
      const w2Entry: Record<string, unknown> = {
        employer_name: data.employer_name,
        employer_ein: data.employer_ein,
        wages_box1: data.wages_box1 ?? 0,
        fed_withheld_box2: data.fed_withheld_box2 ?? 0,
        ss_wages_box3: data.ss_wages_box3 ?? 0,
        ss_tax_box4: data.ss_tax_box4 ?? 0,
        medicare_wages_box5: data.medicare_wages_box5 ?? 0,
        medicare_tax_box6: data.medicare_tax_box6 ?? 0,
        state: data.state,
        state_wages: data.state_wages ?? 0,
        state_tax_withheld: data.state_tax_withheld ?? 0,
        employee_name: data.employee_name,
        ssn_last4: data.ssn_last4,
        document_id: doc.id,
      };

      // Check for duplicates
      const isDuplicate = w2List.some(
        (w) => w.employer_name === w2Entry.employer_name && w.wages_box1 === w2Entry.wages_box1
      );
      if (!isDuplicate) w2List.push(w2Entry);

      totalWithheld += (data.fed_withheld_box2 as number) ?? 0;

      // Extract taxpayer name from W-2 if not set
      const primaryTp = factsData.primary_taxpayer as Record<string, unknown> | undefined;
      if (!primaryTp?.first_name && data.employee_name) {
        const parts = (data.employee_name as string).split(" ");
        if (parts.length >= 2) {
          factsData.primary_taxpayer = {
            ...(primaryTp ?? {}),
            first_name: parts[0],
            last_name: parts.slice(1).join(" "),
          };
        }
      }
    }
  }

  // Build canonical facts
  factsData.income = { ...income, w2: w2List };
  factsData.payments = { fed_income_tax_withheld: totalWithheld };
  factsData.tax_year = caseData.taxYear;

  // Identify unresolved questions
  const unresolved: string[] = [];
  if (!factsData.filing_status) unresolved.push("Filing status has not been determined");
  if (w2List.length === 0) unresolved.push("No W-2 income data found");
  if (!factsData.dependents_asked) unresolved.push("Dependent information has not been collected");

  // Validation errors at normalization time
  const validationErrors: string[] = [];
  for (const w2 of w2List) {
    const wages = (w2.wages_box1 as number) ?? 0;
    const withheld = (w2.fed_withheld_box2 as number) ?? 0;
    if (withheld > wages) {
      const employer = (w2.employer_name as string) ?? "Unknown";
      validationErrors.push(`W-2 from ${employer}: federal withholding ($${withheld.toLocaleString()}) exceeds wages ($${wages.toLocaleString()})`);
    }
  }

  // Save normalized facts
  const newVersion = (latestFact?.version ?? 0) + 1;
  await prisma.taxFact.create({
    data: {
      caseId,
      version: newVersion,
      factsData: factsData as Prisma.InputJsonValue,
      sourceMap: { source: "normalization" } as Prisma.InputJsonValue,
    },
  });

  return {
    tax_facts: factsData,
    unresolved_questions: unresolved,
    validation_errors: validationErrors,
  };
}
