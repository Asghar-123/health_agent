# guardrails/disclaimer_generator.py

MEDICAL_DISCLAIMER = (
    "Please note: I am an AI Health & Wellness Assistant and cannot provide medical "
    "diagnoses, treatment advice, or emergency services. For any medical concerns, "
    "always consult a qualified healthcare professional. In case of an emergency, "
    "please contact emergency services immediately."
)

GENERAL_HEALTH_DISCLAIMER = (
    "Disclaimer: The information provided is for general knowledge and informational "
    "purposes only, and does not constitute medical advice. Always consult with a "
    "qualified healthcare professional before making any decisions about your health or treatment."
)

EMERGENCY_REDIRECT = (
    "I detect that your query might be related to a medical emergency. I cannot provide "
    "emergency services. Please contact your local emergency services immediately "
    "or go to the nearest emergency room."
)

def get_medical_disclaimer() -> str:
    """Returns the standard medical disclaimer."""
    return MEDICAL_DISCLAIMER

def get_general_health_disclaimer() -> str:
    """Returns the general health information disclaimer."""
    return GENERAL_HEALTH_DISCLAIMER

def get_emergency_redirect() -> str:
    """Returns the emergency redirect message."""
    return EMERGENCY_REDIRECT

def add_general_health_disclaimer(response: str) -> str:
    """Appends the general health disclaimer to a given response."""
    return f"{response}\n\n{GENERAL_HEALTH_DISCLAIMER}"
