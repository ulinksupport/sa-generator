from datetime import datetime


def format_current_date_parts() -> dict:
    now = datetime.now()
    return {
        "CURRENT DATE": now.strftime("%Y.%m.%d"),
        "DATE": now.strftime("%d"),
        "MONTH": now.strftime("%b"),
        "YEAR": now.strftime("%Y"),
    }


def build_placeholder_mapping(answer_map: dict) -> dict:
    date_parts = format_current_date_parts()

    mapping = {
        **date_parts,
        "CLIENT NAME": answer_map.get("client_name", ""),
        "CLIENT COUNTRY": answer_map.get("client_country", ""),
        "CLIENT ADDRESS": answer_map.get("client_address", ""),
        "CLIENT CONTACT NAME": answer_map.get("contact_name", ""),
        "CLIENT CONTACT DESIGNATION": answer_map.get("contact_designation", ""),
        "CLIENT CONTACT EMAIL": answer_map.get("contact_email", ""),
        "CLIENT CONTACT PHONE NUMBER": answer_map.get("contact_phone_number", ""),
        "COMPANY REGISTRATION NUMBER": answer_map.get("company_registration_number", ""),
        "CREDIT TERM": answer_map.get("credit_term_days", ""),
        "CONTRACT TERM": answer_map.get("contract_term", ""),
        "RENEWAL TERM": answer_map.get("renewal_term", ""),
        "TERMINATION NOTICE": answer_map.get("termination_notice", ""),
    }

    return mapping