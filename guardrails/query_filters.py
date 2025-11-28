# guardrails/query_filters.py

import re

# Keywords and phrases indicative of medical diagnosis or treatment requests
MEDICAL_DIAGNOSIS_KEYWORDS = [
    r'\bdiagnose\b', r'\bsymptoms\b.*\bmean\b', r'\bwhat is wrong with me\b',
    r'\bdo I have\b', r'\bis this a symptom of\b', r'\bmedical advice\b',
    r'\btreatment for\b', r'\bcure for\b', r'\bmedication for\b',
    r'\bshould I take\b', r'\bwhat should I do for my\b', r'\bdoctor\b.*\bconsult\b',
    r'\bcondition is\b', r'\bmy pain\b', r'\bmy headache\b', r'\bfever\b',
    r'\brash\b', r'\bcough\b', r'\bfatigue\b', r'\bache\b', r'\billness\b'
]

# Keywords and phrases indicative of emergency situations
EMERGENCY_KEYWORDS = [
    r'\bemergency\b', r'\burgent\b', r'\bhelp me now\b', r'\bcall an ambulance\b',
    r'\bchoking\b', r'\bheart attack\b', r'\bstroke\b', r'\bsuicidal\b',
    r'\bhurt myself\b', r'\blife-threatening\b', r'\binjured\b'
]

# Keywords and phrases indicative of off-topic requests (e.g., not health-related)
OFF_TOPIC_KEYWORDS = [
    r'\bhouse construction\b', r'\bbuilding a house\b', r'\barchitect\b',
    r'\bplumbing\b', r'\belectricity\b', r'\broofing\b', r'\bfoundation\b',
    r'\bfinance\b', r'\bstocks\b', r'\binvestment\b', r'\bpolitics\b',
    r'\bgovernment\b', r'\bcar repair\b', r'\bengine\b', r'\bsoftware development\b',
    r'\bprogramming\b', r'\bcomputer\b', r'\bphone\b', r'\bcooking recipe\b',
    r'\bhistory of\b', r'\bgeography of\b', r'\bweather forecast\b'
]

def contains_medical_diagnosis_request(query: str) -> bool:
    """
    Checks if the query contains keywords indicative of a medical diagnosis or treatment request.
    """
    query_lower = query.lower()
    for keyword in MEDICAL_DIAGNOSIS_KEYWORDS:
        if re.search(keyword, query_lower):
            return True
    return False

def contains_emergency_request(query: str) -> bool:
    """
    Checks if the query contains keywords indicative of an emergency situation.
    """
    query_lower = query.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if re.search(keyword, query_lower):
            return True
    return False

def contains_off_topic_request(query: str) -> bool:
    """
    Checks if the query contains keywords indicative of an off-topic request not related to health.
    """
    query_lower = query.lower()
    for keyword in OFF_TOPIC_KEYWORDS:
        if re.search(keyword, query_lower):
            return True
    return False

def contains_sensitive_health_query(query: str) -> bool:
    """
    Combines checks for medical diagnosis and emergency requests.
    """
    return contains_medical_diagnosis_request(query) or contains_emergency_request(query)

