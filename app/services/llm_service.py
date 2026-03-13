from typing import Any

import httpx

from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_APP_NAME,
    OPENROUTER_MODEL,
    OPENROUTER_SITE_URL,
)

INSUFFICIENT_CONTEXT_TOKEN = "__INSUFFICIENT_CONTEXT__"


def _build_context_block(chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        source = chunk.get("source", "uploaded_pdf")
        content = chunk.get("content", "").strip()
        lines.append(f"[{idx}] Source: {source}\n{content}")
    return "\n\n".join(lines)


def generate_grounded_answer(
    user_query: str,
    context_chunks: list[dict[str, Any]],
    faq_fallback: str,
) -> dict[str, Any]:
    if not OPENROUTER_API_KEY or not context_chunks:
        return {"used_llm": False, "answer": "", "reason": "missing_api_key_or_context"}

    context_block = _build_context_block(context_chunks)
    system_prompt = (
        "You are an academic helpdesk assistant. "
        "Answer ONLY using the provided context snippets from uploaded PDFs. "
        f"If the answer is not present in the context, output exactly {INSUFFICIENT_CONTEXT_TOKEN}. "
        "Keep answers concise and factual. Do not invent dates, policies, or links."
    )

    user_prompt = (
        f"Student question: {user_query}\n\n"
        f"PDF context:\n{context_block}\n\n"
        f"FAQ fallback (optional, use only if aligned with PDF context): {faq_fallback}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        return {"used_llm": False, "answer": "", "reason": f"request_failed: {exc}"}

    choices = data.get("choices") or []
    if not choices:
        return {"used_llm": False, "answer": "", "reason": "empty_choices"}

    content = (choices[0].get("message") or {}).get("content", "")
    answer = str(content).strip()
    if not answer:
        return {"used_llm": False, "answer": "", "reason": "empty_answer"}

    if answer == INSUFFICIENT_CONTEXT_TOKEN:
        return {"used_llm": False, "answer": "", "reason": "insufficient_context"}

    return {"used_llm": True, "answer": answer, "reason": "ok"}
