"""Prompt templates for RAG generation with citation enforcement."""

from app.retrieval.dense import ScoredChunk

SYSTEM_PROMPT = """You are a research assistant answering questions about an academic paper.
You MUST cite your sources using bracketed numbers like [1], [2], etc.
Each number corresponds to a context chunk provided below.
Only use information from the provided context. If the context doesn't contain
enough information, say so explicitly.

RULES:
- Every factual claim MUST have at least one citation.
- Use the format [N] immediately after the claim it supports.
- You may cite multiple chunks for one claim: [1][3].
- Do NOT fabricate information not in the context.
- Respond in clear, concise academic prose.
- If asked about something not covered in the context, say "The provided context does not contain information about this topic.\""""


def build_user_prompt(
    question: str,
    chunks: list[ScoredChunk],
    conversation_history: list[dict] | None = None,
) -> list[dict]:
    """
    Build the message list for the LLM call.

    Returns list of {role, content} dicts including conversation history.
    """
    # Build context block from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks):
        section_info = f", Section: {chunk.section_heading}" if chunk.section_heading else ""
        context_parts.append(
            f"[{i + 1}] (Page {chunk.page_number}{section_info})\n{chunk.content}"
        )
    context_block = "\n\n".join(context_parts)

    messages = []

    # Add conversation history if present
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current question with context
    user_message = f"""CONTEXT:
{context_block}

QUESTION: {question}"""

    messages.append({"role": "user", "content": user_message})

    return messages
