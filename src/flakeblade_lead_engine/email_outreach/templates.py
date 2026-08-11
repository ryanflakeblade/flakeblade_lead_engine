from __future__ import annotations


def dealer_intro_subject(company_name: str) -> str:
    name = company_name.strip() if company_name else "your team"
    return f"Winter equipment question for {name}"


def dealer_intro_email(company_name: str, contact_name: str = "") -> str:
    greeting = f"Hi {contact_name.strip()}," if contact_name else "Hi,"
    company = company_name.strip() if company_name else "your company"
    return (
        f"{greeting}\n\n"
        "I am reaching out from Flakeblade. We are building snow removal equipment "
        "for property maintenance, condo, parking, and landscaping teams around Quebec.\n\n"
        f"I saw {company} listed in the RGCQ corporate member directory and wanted to ask: "
        "do you handle winter snow removal directly, or do you usually subcontract it?\n\n"
        "If you handle it directly, I would be happy to share details. If it is subcontracted, "
        "could you point me to the right snow removal contractor or operations contact?\n\n"
        "Best,\n"
        "Flakeblade Team"
    )

