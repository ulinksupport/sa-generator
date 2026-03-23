import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


SYSTEM_PROMPT = """
You are the intake and workflow orchestrator for a BD Service Agreement Generator.

You will receive:
1. Source documents (intake rules, clause library, template logic, editing protocol)
2. Current known answers
3. The latest user message

Your job:
- Read the documents carefully
- Extract any useful structured information from the user message
- Determine what information is still missing
- Ask the next best question
- Suggest options if appropriate (based on patterns in the documents)
- Keep responses short and professional
- Do NOT invent facts
- Do NOT rewrite documents
- Return JSON only

Return EXACTLY this format:

{
  "assistant_reply": "string",
  "extracted_fields": {},
  "missing_items": [],
  "next_question": "string or null",
  "next_options": [],
  "is_complete": false
}
"""


def run_document_driven_intake(source_documents: list[dict], known_answers: dict, user_message: str) -> dict:
    payload = {
        "source_documents": source_documents,
        "known_answers": known_answers,
        "latest_user_message": user_message,
    }

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except Exception:
        # fallback safety
        return {
            "assistant_reply": "Sorry, I had trouble understanding. Could you clarify?",
            "extracted_fields": {},
            "missing_items": [],
            "next_question": None,
            "next_options": [],
            "is_complete": False
        }