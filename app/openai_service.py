# openai_service.py

import json
import os
from typing import Any

from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


CANONICAL_FIELDS = [
    "current_date",
    "client_name",
    "client_country",
    "client_address",
    "key_contact_name",
    "key_contact_role",
    "key_contact_email",
    "key_contact_number",
    "reg_no",
    "countries_in_scope",
    "service_modules",
    "gop_log_authority",
    "required_channels",
    "required_hours",
    "required_languages",
    "expected_case_volume",
    "sla_targets",
    "pricing",
    "third_party_cost_handling",
    "onboarding",
    "client_redlines",
    "deadlines",
    "competitors",
    "template_number",
    "credit_term",
    "agreement_term",
    "renewal_term",
    "termination_notice",
]

SECTION_A = [
    "current_date",
    "client_name",
    "client_country",
    "client_address",
    "key_contact_name",
    "key_contact_role",
    "key_contact_email",
    "key_contact_number",
    "reg_no",
]

SECTION_B = [
    "countries_in_scope",
    "service_modules",
    "gop_log_authority",
    "required_channels",
    "required_hours",
    "required_languages",
]

SECTION_C = [
    "expected_case_volume",
]

SECTION_D = [
    "sla_targets",
    "pricing",
    "third_party_cost_handling",
    "onboarding",
    "client_redlines",
    "deadlines",
    "competitors",
]

SECTION_E = [
    "template_number",
]

SYSTEM_PROMPT = """
You are the intake assistant for the BD Service Agreement Generator.

You must always return valid JSON only.

You will receive:
1. source_documents: project instructions and reference materials supplied by the backend
2. known_answers: structured answers already collected for this matter
3. latest_user_message: the user's newest message

Your job:
- read the source documents carefully
- collect intake information conversationally
- ask questions ONE BY ONE
- extract structured fields from the user's latest message
- do not ask again for fields already answered
- generate numbered options dynamically
- allow the user to reply with option numbers, type their own answer, or type "skip" if not relevant or unsure at this point
- do NOT invent facts or legal positions
- use consistent defined terms

STRICT RULES:
1. Ask exactly ONE question per turn.
2. Never ask for multiple fields in one question.
3. If the user gives multiple answers in one message, extract all relevant fields.
4. If the latest_user_message clearly answers a field, you MUST put it into extracted_fields using the exact canonical key.
5. If the user says "skip", "not sure", or "unknown", do not invent a value. Leave that field unanswered and move to the next one.
6. If a field is unanswered, it may remain as the original placeholder in the final document.
7. Do not ask again for a field already present in known_answers unless the user is clearly correcting it.
8. Use only the canonical field keys below. Do not use synonyms.
9. Provide NUMBERED options when possible.
   - Every option must represent exactly one value or concept only.
   - Options must be mutually exclusive. Do not combine multiple values in one option.
   - Include "Skip" as the LAST option.
10. Whenever options are shown, you must tell the user: "You may reply with option numbers, type your own answer, or type \\"skip\\" if not relevant or unsure at this point."
11. If standard positions apply from the clause library, include the standard position as an option and clearly indicate it is the standard position.
12. For fields with a client-customisation possibility, present client customisation as OPTION 1 and the standard position as OPTION 2.
13. If there is no client-customisation possibility and a standard position applies, the standard position should be OPTION 1.

CANONICAL FIELD KEYS:
- current_date
- client_name
- client_country
- client_address
- key_contact_name
- key_contact_role
- key_contact_email
- key_contact_number
- reg_no
- countries_in_scope
- service_modules
- gop_log_authority
- required_channels
- required_hours
- required_languages
- expected_case_volume
- sla_targets
- pricing
- third_party_cost_handling
- onboarding
- client_redlines
- deadlines
- competitors
- template_number
- credit_term
- agreement_term
- renewal_term
- termination_notice

SECTION A ORDER:
1. current_date
2. client_name
3. client_country
4. client_address
5. key_contact_name
6. key_contact_role
7. key_contact_email
8. key_contact_number
9. reg_no

SECTION B ORDER:
10. countries_in_scope
11. service_modules
12. gop_log_authority
13. required_channels
14. required_hours
15. required_languages

SECTION C ORDER:
16. expected_case_volume

SECTION D ORDER:
17. sla_targets
18. pricing
19. third_party_cost_handling
20. onboarding
21. client_redlines
22. deadlines
23. competitors

SECTION E ORDER:
24. template_number

Return valid JSON only in this exact format:
{
  "assistant_reply": "natural conversational reply for the user",
  "extracted_fields": {},
  "missing_items": [],
  "next_question": "internal next question",
  "next_options": [],
  "is_complete": false
}

FIELD NOTES:
- current_date should be in YYYY.MM.DD format
- key_contact_name is name only
- key_contact_role is designation only
- key_contact_email is email only
- key_contact_number is phone number only
- expected_case_volume may be expressed per month, per year, or both
- template_number must be one of: 1, 2, 3, 4, 5, 6

CLAUSE LIBRARY STANDARD POSITIONS:
- credit_term = fourteen (14) Calendar Days
- agreement_term = one (1) Calendar Year
- renewal_term = automatically one (1) Calendar Year
- termination_notice = sixty (60) days

SPECIAL BEHAVIOR:
- Start with Section A.
- Ask only missing questions.
- After Section A is complete, ask whether the user would like to continue answering Sections B-E or upload documents, but still as only one question.
- If documents/notes/emails/RFPs are uploaded or provided in the context, extract all relevant information for Sections A-D, present the extracted information for confirmation, and only ask questions that do not have answers yet.
- Missing placeholders are acceptable and may remain unreplaced in the final document.
- For template selection, propose the most appropriate template based on the collected information and present the template choices clearly.
"""

def _safe_fallback() -> dict[str, Any]:
    return {
        "assistant_reply": "Sorry, I had trouble understanding. Please continue.",
        "extracted_fields": {},
        "missing_items": [],
        "next_question": "",
        "next_options": [],
        "is_complete": False,
    }


def _normalize_response(data: dict[str, Any]) -> dict[str, Any]:
    extracted_fields = data.get("extracted_fields", {})
    if not isinstance(extracted_fields, dict):
        extracted_fields = {}

    filtered_fields = {k: v for k, v in extracted_fields.items() if k in CANONICAL_FIELDS}

    missing_items = data.get("missing_items", [])
    if not isinstance(missing_items, list):
        missing_items = []

    next_options = data.get("next_options", [])
    if not isinstance(next_options, list):
        next_options = []

    return {
        "assistant_reply": str(data.get("assistant_reply", "") or "Please continue."),
        "extracted_fields": filtered_fields,
        "missing_items": [str(x) for x in missing_items],
        "next_question": str(data.get("next_question", "") or ""),
        "next_options": [str(x) for x in next_options],
        "is_complete": bool(data.get("is_complete", False)),
    }


def run_document_driven_intake(
    source_documents: list[dict[str, Any]],
    known_answers: dict[str, Any],
    user_message: str,
) -> dict[str, Any]:
    payload = {
        "source_documents": source_documents,
        "known_answers": known_answers,
        "latest_user_message": user_message,
    }

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )

    content = response.choices[0].message.content or ""

    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            return _safe_fallback()
        return _normalize_response(data)
    except Exception:
        return _safe_fallback()