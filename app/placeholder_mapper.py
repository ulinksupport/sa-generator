# placeholder_mapper.py

from __future__ import annotations

from datetime import datetime
from typing import Any


DEFAULT_CREDIT_TERM = "fourteen (14) Calendar Days"
DEFAULT_AGREEMENT_TERM = "one (1) Calendar Year"
DEFAULT_RENEWAL_TERM = "automatically one (1) Calendar Year"
DEFAULT_TERMINATION_NOTICE = "sixty (60) days"


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def _parse_current_date(raw: str) -> datetime:
    raw = (raw or "").strip()
    if not raw:
        return datetime.today()

    for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    return datetime.today()


def build_placeholder_mapping(answer_map: dict[str, Any]) -> dict[str, str]:
    def get(key: str, default: str = "") -> str:
        value = answer_map.get(key, default)
        text = _stringify(value)
        return text if text else default

    dt = _parse_current_date(get("current_date"))

    current_date_text = get("current_date")
    if not current_date_text:
        current_date_text = dt.strftime("%Y.%m.%d")

    mapping = {
        "{{MONTH}}": dt.strftime("%B"),
        "{{YEAR}}": dt.strftime("%Y"),
        "{{CURRENT_DATE}}": current_date_text,
        "{{CLIENT NAME}}": get("client_name"),
        "{{CLIENT_NAME}}": get("client_name"),
        "{{CLIENT COUNTRY}}": get("client_country"),
        "{{REG NO}}": get("reg_no"),
        "{{ADDRESS}}": get("client_address"),
        "{{CLIENT ADDRESS}}": get("client_address"),
        "{{KEY CONTACT NAME}}": get("key_contact_name"),
        "{{CONTACT NAME}}": get("key_contact_name"),
        "{{KEY CONTACT ROLE}}": get("key_contact_role"),
        "{{CONTACT ROLE}}": get("key_contact_role"),
        "{{KEY CONTACT EMAIL}}": get("key_contact_email"),
        "{{CONTACT EMAIL}}": get("key_contact_email"),
        "{{KEY CONTACT NUMBER}}": get("key_contact_number"),
        "{{CONTACT NUMBER}}": get("key_contact_number"),
        "{{CREDIT TERM}}": get("credit_term", DEFAULT_CREDIT_TERM),
        "{{AGREEMENT TERM}}": get("agreement_term", DEFAULT_AGREEMENT_TERM),
        "{{RENEWAL TERM}}": get("renewal_term", DEFAULT_RENEWAL_TERM),
        "{{TERMINATION NOTICE}}": get("termination_notice", DEFAULT_TERMINATION_NOTICE),
    }

    return mapping