# guardrails/guardrail_manager.py

from typing import Tuple, Optional
from guardrails.query_filters import (
    contains_emergency_request,
    contains_medical_diagnosis_request,
    contains_off_topic_request # Import the new filter
)
from guardrails.disclaimer_generator import (
    get_emergency_redirect,
    get_medical_disclaimer,
    add_general_health_disclaimer
)

class GuardrailManager:
    OFF_TOPIC_REFUSAL_MESSAGE = (
        "I specialize in health, nutrition, workout, and biology information. "
        "I cannot provide advice on topics like house construction, finance, or politics. "
        "Please ask me a health-related question!"
    )

    def __init__(self):
        self.medical_disclaimer_text = get_medical_disclaimer()
        self.emergency_redirect_text = get_emergency_redirect()

    def pre_process_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Processes the incoming query through guardrails.
        Returns (True, None) if the query passes, or (False, refusal_message) if blocked.
        """
        if contains_emergency_request(query):
            return False, self.emergency_redirect_text
        if contains_medical_diagnosis_request(query):
            return False, self.medical_disclaimer_text
        if contains_off_topic_request(query): # New off-topic check
            return False, self.OFF_TOPIC_REFUSAL_MESSAGE
        return True, None

    def post_process_response(self, response: str, needs_disclaimer: bool = True) -> str:
        """
        Applies post-processing guardrails to the response, such as adding disclaimers.
        """
        if needs_disclaimer:
            return add_general_health_disclaimer(response)
        return response
