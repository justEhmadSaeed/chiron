import os
import logging
import warnings

# Suppress annoying third-party library logs
logging.getLogger("chromadb").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
logging.getLogger("langchain_google_genai").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Configure a clean, professional logger
class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[90m",    # Gray
        logging.INFO: "\033[92m",     # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",    # Red
        logging.CRITICAL: "\033[1;91m" # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)

logger = logging.getLogger("research_agent")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(console_handler)

os.environ["ANONYMIZED_TELEMETRY"] = "False"
warnings.filterwarnings("ignore")

from chiron_backend.common.config import get_settings
from chiron_backend.agents.research.graph import build_graph

def run_test_pipeline():
    print("\n" + "="*80)
    print("\033[1;96m          AI RESEARCH VALIDATION & REMEDIATION PIPELINE\033[0m")
    print("="*80 + "\n")

    user_prompt = "Explore the novelty of using contrastive learning combined with graph-based decoders for topological road network extraction to solve connectivity gaps in satellite imagery."
    
    print(f"\033[1;93m[TARGET RESEARCH PROMPT]\033[0m\n{user_prompt}\n")

    logger.info("Initializing Graph Workflow...")
    app_graph = build_graph()

    initial_state = {
        "research_prompt": user_prompt,
        "pimo_json": {},
        "adversarial_json": {},
        "search_evidence": "",
        "remediation_suggestion": "",
        "final_client_report": ""
    }

    final_report = None

    try:
        logger.info("Executing Pipeline. Please wait...")
        
        for output in app_graph.stream(initial_state):
            for node_name, state_update in output.items():
                logger.info(f"✔ Node Completed: [{node_name.upper()}]")
                
                # Show key updates elegantly
                if node_name == "pimo_generator":
                    logger.debug("  -> Initial Protocol & Hypothesis Generated.")
                
                elif node_name == "adversarial_evaluator":
                    adv_output = state_update.get("adversarial_json", {})
                    if adv_output:
                        status = "✅ NOVEL" if adv_output.get("signal") == "not_found" else "❌ NOT NOVEL"
                        logger.debug(f"  -> Evaluation Result: {status} | Score: {adv_output.get('noveltyScore')}")
                        if adv_output.get("reasoning"):
                            logger.info(f"  -> Adversarial Reasoning: {adv_output.get('reasoning')}")
                
                elif node_name == "remediation_agent":
                    logger.debug("  -> Remediation Strategy Generated.")

                elif node_name == "qc_router":
                    logger.debug("  -> Final QC Report Generated.")

                # Capture report if generated
                if "final_client_report" in state_update and state_update["final_client_report"]:
                    final_report = state_update["final_client_report"]

        print("\n" + "="*80)
        print("\033[1;92mFINAL CLIENT REPORT\033[0m")
        print("="*80)
        if final_report:
            print(f"\n{final_report}\n")
            print("="*80 + "\n")
        else:
            logger.error("Pipeline finished but no final report was generated.")

    except Exception as e:
        logger.exception(f"Pipeline crashed due to an error: {e}")

if __name__ == "__main__":
    settings = get_settings()
    if not settings.gemini_api_key or not settings.tavily_api_key:
        print("\033[91m[ERROR] gemini_api_key and tavily_api_key must be set in the environment.\033[0m")
        exit(1)
        
    run_test_pipeline()
