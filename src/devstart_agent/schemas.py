PUBLIC_FIELDS = ("code", "name", "category", "version", "difficulty", "estimatedDays",
    "background", "goal", "publicRequirements", "technicalConstraints", "deliverables", "extensionTask")

def project(row, fields):
    return {k: row.get(k) for k in fields}

def public_challenge(row):
    # StaffChallenge is deliberately unwrapped only through publicContent.
    return project(row.get("publicContent", row), PUBLIC_FIELDS)
