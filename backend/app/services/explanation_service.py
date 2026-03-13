import json

import structlog
from openai import AsyncOpenAI

from app.config import settings

logger = structlog.get_logger()

EXPLANATION_SYSTEM_PROMPT = """You are a tax explanation assistant. Your job is to explain ALREADY COMPUTED tax results in plain, friendly language.

Rules:
1. Only explain values that are provided. Do NOT compute or verify any numbers.
2. Use simple language a non-accountant can understand.
3. Be concise but thorough.
4. Reference specific dollar amounts from the results.
5. If there's a refund, explain why in positive terms.
6. If there's a balance owed, explain it matter-of-factly without alarm.
7. Do NOT give tax advice or suggest deductions they didn't take."""


async def generate_explanation(results: dict) -> str:
    """Generate a plain-language explanation of computed tax results."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    results_summary = json.dumps(results, indent=2)

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Explain these tax computation results to the taxpayer:\n\n{results_summary}",
            },
        ],
        temperature=0.5,
        max_tokens=800,
    )

    explanation = response.choices[0].message.content
    logger.info("explanation_generated", length=len(explanation))
    return explanation
