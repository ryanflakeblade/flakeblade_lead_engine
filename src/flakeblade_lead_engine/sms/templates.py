from __future__ import annotations


def dealer_intro_message(company_name: str) -> str:
    name = company_name.strip() if company_name else "there"
    return (
        f"Hi {name}, Flakeblade helps dealers reach snow removal and lawn care companies "
        "across Canada by SMS. Reply YES to learn more, NO to opt out."
    )

