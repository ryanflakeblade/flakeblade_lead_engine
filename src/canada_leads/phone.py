from __future__ import annotations

import re


def to_e164(phone: str | None) -> str:
    if not phone:
        return ""

    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return ""

