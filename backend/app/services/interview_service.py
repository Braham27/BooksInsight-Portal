import json
import uuid

import structlog
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.case import Case
from app.models.chat_message import ChatMessage, MessageRole
from app.models.document import Document
from app.models.tax_facts import TaxFact

logger = structlog.get_logger()

# Interview steps and the facts each step needs to collect
INTERVIEW_STEPS = [
    {
        "name": "greeting",
        "description": "Greet the user and ask them to upload documents or start answering questions",
        "required_facts": [],
    },
    {
        "name": "filing_status",
        "description": "Determine filing status",
        "required_facts": ["filing_status"],
    },
    {
        "name": "taxpayer_info",
        "description": "Collect taxpayer name and basic info",
        "required_facts": ["primary_taxpayer.first_name", "primary_taxpayer.last_name"],
    },
    {
        "name": "income_review",
        "description": "Review W-2 income and ask about additional income sources",
        "required_facts": ["income.w2"],
    },
    {
        "name": "dependents",
        "description": "Ask about dependents",
        "required_facts": ["dependents_asked"],
    },
    {
        "name": "deductions",
        "description": "Confirm standard deduction (MVP only supports standard)",
        "required_facts": ["deduction_confirmed"],
    },
    {
        "name": "missing_docs",
        "description": "Check for any missing documents",
        "required_facts": ["docs_complete"],
    },
    {
        "name": "complete",
        "description": "Interview is complete, ready for computation",
        "required_facts": [],
    },
]

INTERVIEW_SYSTEM_PROMPT = """You are a friendly tax preparation assistant for a US federal tax system.
Your role is to interview the user and collect tax information step by step.

Rules:
1. Ask ONE question at a time. Be conversational and clear.
2. NEVER compute taxes or make tax decisions.
3. NEVER determine eligibility for credits or deductions on your own.
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
- "step_complete": boolean indicating if this step's required facts are now collected
"""

STEP_INSTRUCTIONS = {
    "greeting": "Welcome the user warmly. Tell them you can help with their US federal taxes. Ask if they have their W-2 ready to upload, or if they'd prefer to answer questions first.",
    "filing_status": "Ask about their filing status. Explain the options in plain language: Single, Married Filing Jointly (MFJ), Married Filing Separately (MFS), Head of Household (HOH), or Qualifying Surviving Spouse (QSS). Extract the chosen status.",
    "taxpayer_info": "Ask for the taxpayer's name. If we already have it from a W-2, confirm it.",
    "income_review": "If W-2 data exists from document upload, summarize what was found and ask the user to confirm. If no W-2 uploaded, ask if they have W-2 income and collect the amounts. Ask if they have any other W-2s.",
    "dependents": "Ask if the user has any dependents (children or qualifying relatives). Collect basic info for each: name, date of birth, relationship. If none, that's fine.",
    "deductions": "For this version, we only support the standard deduction. Let the user know we'll apply the standard deduction. Ask if they're over 65 or legally blind (as these affect the standard deduction amount).",
    "missing_docs": "Review what we have and ask if there's anything else. Remind them this MVP only handles W-2 income. If they mention 1099s or other income, let them know that's coming in a future version.",
    "complete": "Summarize everything collected and let the user know we're ready to calculate their federal tax estimate.",
}


def _get_current_step(facts_data: dict) -> dict:
    """Determine which interview step we're on based on collected facts."""
    for step in INTERVIEW_STEPS:
        if step["name"] == "greeting" and facts_data.get("greeting_done"):
            continue
        if step["name"] == "complete":
            return step

        all_facts_present = True
        for fact in step["required_facts"]:
            parts = fact.split(".")
            current = facts_data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    all_facts_present = False
                    break
            if not all_facts_present:
                break

        if not all_facts_present:
            return step

    return INTERVIEW_STEPS[-1]  # complete


def _compute_progress(facts_data: dict) -> dict:
    """Compute interview progress."""
    total_steps = len(INTERVIEW_STEPS) - 1  # exclude "complete"
    completed = []
    remaining = []

    for step in INTERVIEW_STEPS:
        if step["name"] == "complete":
            continue
        all_present = True
        for fact in step["required_facts"]:
            parts = fact.split(".")
            current = facts_data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    all_present = False
                    break
            if not all_present:
                break

        if all_present and (step["required_facts"] or step["name"] == "greeting" and facts_data.get("greeting_done")):
            completed.append(step["name"])
        elif not step["required_facts"] and step["name"] == "greeting" and facts_data.get("greeting_done"):
            completed.append(step["name"])
        else:
            remaining.append(step["name"])

    current_step = _get_current_step(facts_data)
    pct = int((len(completed) / max(total_steps, 1)) * 100)

    return {
        "current_step": current_step["name"],
        "completion_pct": min(pct, 100),
        "steps_completed": completed,
        "steps_remaining": remaining,
    }


async def get_chat_history(db: AsyncSession, case_id: str) -> list[dict]:
    """Get chat history for a case."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.case_id == case_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role.value, "content": m.content} for m in messages]


async def get_current_facts(db: AsyncSession, case_id: str) -> dict:
    """Get the latest tax facts for a case."""
    result = await db.execute(
        select(TaxFact)
        .where(TaxFact.case_id == case_id)
        .order_by(TaxFact.version.desc())
        .limit(1)
    )
    fact = result.scalar_one_or_none()
    return fact.facts_data if fact else {}


async def process_message(
    db: AsyncSession,
    case_id: str,
    user_message: str,
) -> dict:
    """Process a user message and return the assistant's response."""
    case = await db.get(Case, case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")

    # Save user message
    user_msg = ChatMessage(
        case_id=case_id,
        role=MessageRole.USER,
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # Get current state
    facts_data = await get_current_facts(db, case_id)
    chat_history = await get_chat_history(db, case_id)
    current_step = _get_current_step(facts_data)

    # Build LLM prompt
    missing_info = []
    for fact in current_step.get("required_facts", []):
        parts = fact.split(".")
        current = facts_data
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if not found:
            missing_info.append(fact)

    system_prompt = INTERVIEW_SYSTEM_PROMPT.format(
        current_step=current_step["name"],
        step_description=current_step["description"],
        known_facts=json.dumps(facts_data, indent=2) if facts_data else "None yet",
        missing_info=", ".join(missing_info) if missing_info else "None",
        step_instructions=STEP_INSTRUCTIONS.get(current_step["name"], ""),
    )

    # Call OpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Build messages for LLM (include recent history for context)
    llm_messages = [{"role": "system", "content": system_prompt}]
    # Include last 10 messages for context
    for msg in chat_history[-10:]:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=llm_messages,
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=1000,
    )

    result_text = response.choices[0].message.content
    result = json.loads(result_text)

    assistant_text = result.get("message", "I'm not sure how to respond to that.")
    extracted_facts = result.get("extracted_facts")
    step_complete = result.get("step_complete", False)

    # Update facts if we extracted anything
    structured_output = None
    if extracted_facts:
        # Merge extracted facts into existing facts
        updated_facts = {**facts_data}
        for key, value in extracted_facts.items():
            if isinstance(value, dict) and key in updated_facts and isinstance(updated_facts[key], dict):
                updated_facts[key] = {**updated_facts[key], **value}
            else:
                updated_facts[key] = value

        if step_complete:
            # Mark the greeting as done
            if current_step["name"] == "greeting":
                updated_facts["greeting_done"] = True

        # Save updated facts
        latest = await db.execute(
            select(TaxFact)
            .where(TaxFact.case_id == case_id)
            .order_by(TaxFact.version.desc())
            .limit(1)
        )
        latest_fact = latest.scalar_one_or_none()
        new_version = (latest_fact.version + 1) if latest_fact else 1

        new_fact = TaxFact(
            case_id=case_id,
            version=new_version,
            facts_data=updated_facts,
            source_map={"source": "interview", "step": current_step["name"]},
        )
        db.add(new_fact)
        await db.flush()

        structured_output = extracted_facts

        # Update case filing status if extracted
        if "filing_status" in extracted_facts:
            case.filing_status = extracted_facts["filing_status"]
        if "primary_taxpayer" in extracted_facts:
            tp = extracted_facts["primary_taxpayer"]
            name_parts = []
            if tp.get("first_name"):
                name_parts.append(tp["first_name"])
            if tp.get("last_name"):
                name_parts.append(tp["last_name"])
            if name_parts:
                case.taxpayer_name = " ".join(name_parts)
    elif step_complete and current_step["name"] == "greeting":
        updated_facts = {**facts_data, "greeting_done": True}
        latest = await db.execute(
            select(TaxFact)
            .where(TaxFact.case_id == case_id)
            .order_by(TaxFact.version.desc())
            .limit(1)
        )
        latest_fact = latest.scalar_one_or_none()
        new_version = (latest_fact.version + 1) if latest_fact else 1
        new_fact = TaxFact(
            case_id=case_id, version=new_version, facts_data=updated_facts,
            source_map={"source": "interview", "step": "greeting"},
        )
        db.add(new_fact)
        await db.flush()

    # Save assistant message
    assistant_msg = ChatMessage(
        case_id=case_id,
        role=MessageRole.ASSISTANT,
        content=assistant_text,
        structured_output=structured_output,
    )
    db.add(assistant_msg)
    await db.flush()

    # Compute progress
    final_facts = await get_current_facts(db, case_id)
    progress = _compute_progress(final_facts)

    return {
        "assistant_message": assistant_msg,
        "structured_update": structured_output,
        "progress": progress,
        "unresolved_questions": missing_info,
    }


async def normalize_facts(
    db: AsyncSession,
    case_id: str,
) -> dict:
    """Merge document-extracted data and interview answers into canonical TaxFacts."""
    case = await db.get(Case, case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")

    # Get latest interview facts
    facts_data = await get_current_facts(db, case_id)

    # Get all extracted documents
    result = await db.execute(
        select(Document).where(
            Document.case_id == case_id,
            Document.status.in_(["extracted", "verified"]),
        )
    )
    documents = result.scalars().all()

    # Merge document data into facts
    w2_list = facts_data.get("income", {}).get("w2", [])
    total_withheld = 0.0

    for doc in documents:
        if doc.doc_type == "W2" and doc.extracted_data:
            data = doc.extracted_data
            w2_entry = {
                "employer_name": data.get("employer_name"),
                "employer_ein": data.get("employer_ein"),
                "wages_box1": data.get("wages_box1", 0),
                "fed_withheld_box2": data.get("fed_withheld_box2", 0),
                "ss_wages_box3": data.get("ss_wages_box3", 0),
                "ss_tax_box4": data.get("ss_tax_box4", 0),
                "medicare_wages_box5": data.get("medicare_wages_box5", 0),
                "medicare_tax_box6": data.get("medicare_tax_box6", 0),
                "state": data.get("state"),
                "state_wages": data.get("state_wages", 0),
                "state_tax_withheld": data.get("state_tax_withheld", 0),
                "employee_name": data.get("employee_name"),
                "ssn_last4": data.get("ssn_last4"),
                "document_id": str(doc.id),
            }

            # Check for duplicates (same employer + same wages)
            is_duplicate = any(
                w.get("employer_name") == w2_entry["employer_name"]
                and w.get("wages_box1") == w2_entry["wages_box1"]
                for w in w2_list
            )
            if not is_duplicate:
                w2_list.append(w2_entry)

            total_withheld += data.get("fed_withheld_box2", 0)

            # Extract taxpayer name from W-2 if not set
            if not facts_data.get("primary_taxpayer", {}).get("first_name"):
                if data.get("employee_name"):
                    parts = data["employee_name"].split()
                    if len(parts) >= 2:
                        facts_data.setdefault("primary_taxpayer", {})
                        facts_data["primary_taxpayer"]["first_name"] = parts[0]
                        facts_data["primary_taxpayer"]["last_name"] = " ".join(parts[1:])

    # Build canonical facts
    facts_data.setdefault("income", {})
    facts_data["income"]["w2"] = w2_list
    facts_data.setdefault("payments", {})
    facts_data["payments"]["fed_income_tax_withheld"] = total_withheld
    facts_data["tax_year"] = case.tax_year

    # Identify unresolved questions
    unresolved = []
    if not facts_data.get("filing_status"):
        unresolved.append("Filing status has not been determined")
    if not w2_list:
        unresolved.append("No W-2 income data found")
    if not facts_data.get("dependents_asked"):
        unresolved.append("Dependent information has not been collected")

    # Identify validation errors at normalization time
    validation_errors = []
    for w2 in w2_list:
        wages = w2.get("wages_box1", 0)
        withheld = w2.get("fed_withheld_box2", 0)
        if withheld > wages:
            employer = w2.get("employer_name", "Unknown")
            validation_errors.append(
                f"W-2 from {employer}: federal withholding (${withheld:,.2f}) exceeds wages (${wages:,.2f})"
            )

    # Save normalized facts
    latest = await db.execute(
        select(TaxFact)
        .where(TaxFact.case_id == case_id)
        .order_by(TaxFact.version.desc())
        .limit(1)
    )
    latest_fact = latest.scalar_one_or_none()
    new_version = (latest_fact.version + 1) if latest_fact else 1

    new_fact = TaxFact(
        case_id=case_id,
        version=new_version,
        facts_data=facts_data,
        source_map={"source": "normalization"},
    )
    db.add(new_fact)
    await db.flush()

    return {
        "tax_facts": facts_data,
        "unresolved_questions": unresolved,
        "validation_errors": validation_errors,
    }
