from typing import TypedDict, Dict, Any

class AgentState(TypedDict, total=False):
    research_prompt: str
    experiment_id: str       # Firebase UUID for this hypothesis run

    # Outputs from PIMO Architect
    pimo_json: Dict[str, Any]

    # Outputs from Adversarial Evaluator
    adversarial_json: Dict[str, Any]
    search_evidence: str

    # Output from Remediation
    remediation_suggestion: str

    # Final Output
    final_client_report: str
