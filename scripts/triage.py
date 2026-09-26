import argparse
import sys
import logging

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.redact.pseudonymizer import Pseudonymizer
from core.redact.report import generate_redaction_report
from core.agent import create_research_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def triage_log(log_text: str):
    # 1. Redact the log
    pseudonymizer = Pseudonymizer()
    redacted_log = pseudonymizer.redact(log_text)
    audit_report = generate_redaction_report(pseudonymizer.get_report())
    
    logger.info("=== Redaction Audit Report ===")
    logger.info(audit_report)
    
    # 2. Invoke the agent
    logger.info("=== Initializing AI Triage Agent ===")
    try:
        agent = create_research_agent(reload=False)
        chat = agent.get_chat_handler()
        
        prompt = (
            "Analyze the following wireless log snippet. Identify any cause codes, reason codes, "
            "or timers that indicate a failure. Search the specifications to explain what the failure "
            "means and suggest next steps for triage.\n\n"
            f"LOG SNIPPET:\n{redacted_log}"
        )
        
        logger.info("=== Querying Agent (this may take a moment if Ollama needs to load) ===")
        response = chat(prompt)
        
        logger.info("=== Agent Response ===")
        print(response)
        
    except Exception as e:
        logger.error(f"Failed to query agent: {e}")
        logger.error("Please ensure Ollama is running and the LanceDB index is populated.")

def main():
    parser = argparse.ArgumentParser(description="Triage a wireless log snippet using Agentic RAG")
    parser.add_argument("--log", type=str, help="Raw log string to triage")
    parser.add_argument("--file", type=str, help="Path to log file to triage")
    
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, "r") as f:
            log_text = f.read()
    elif args.log:
        log_text = args.log
    else:
        # Example from scenario
        log_text = """14:32:01.123 [NAS] Tx ATTACH REQUEST (IMSI=001011234567890)
14:32:01.450 [NAS] Rx ATTACH REJECT (EMM Cause: 15)
14:32:01.455 [NAS] EMM state changed to EMM-DEREGISTERED.PLMN-SEARCH"""
        logger.info("No log provided, using default Attach Reject example.")

    triage_log(log_text)

if __name__ == "__main__":
    main()
