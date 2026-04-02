
"""
Module 6: MainOrchestrator
The primary entry point for the Nion Agentic Engine.
Handles CLI arguments, JSON parsing, and coordinates the orchestration pipeline.
"""

import json
import sys
import argparse
from pathlib import Path

from intent_analyzer import IntentAnalyzer
from l1_planner import L1Planner
from l2_router import L2Router
from output_formatter import OutputFormatter

# ─────────────────────────────────────────────
# CORE ORCHESTRATION PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(message: dict) -> str:
    """
    Coordinates the multi-layer transformation of a raw message 
    into a high-fidelity Nion Orchestration Map.
    """
    # Layer 1: Strategic Analysis
    intent  = IntentAnalyzer.analyze(message)
    
    # Layer 2: Strategic Planning (Visibility Enforced)
    plan    = L1Planner.plan(intent, message)
    
    # Layer 3: Tactical Routing (L2 Domain Coordination)
    routed  = L2Router.route_all(plan.tasks)
    
    # Layer 4: High-Fidelity Rendering
    return OutputFormatter.render(message, plan, routed)

# ─────────────────────────────────────────────
# CLI INTERFACE
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Nion Agentic Orchestration Engine")
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument("--file", help="Path to a specific JSON message file")
    group.add_argument("--json", help="Inline JSON message string for direct processing")
    group.add_argument("--suite", help="Path to a JSON test suite (defaults to test_cases.json)", 
                       default="test_cases.json")
    
    args = parser.parse_args()

    # Scenario 1: Process a single file
    if args.file:
        _process_single_file(args.file)

    # Scenario 2: Process raw JSON string
    elif args.json:
        _process_raw_json(args.json)

    # Scenario 3: Run the Test Suite (Default)
    else:
        _run_test_suite(args.suite)

def _process_single_file(filepath: str):
    try:
        with open(filepath, 'r') as f:
            message = json.load(f)
            print(run_pipeline(message))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Could not process file '{filepath}': {e}", file=sys.stderr)

def _process_raw_json(json_str: str):
    try:
        message = json.loads(json_str)
        print(run_pipeline(message))
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON string provided.", file=sys.stderr)

def _run_test_suite(suite_path: str):
    path = Path(suite_path)
    if not path.exists():
        print(f"ERROR: Test suite '{suite_path}' not found. Please create it or provide a path.")
        return

    try:
        with open(path, 'r') as f:
            suite = json.load(f)
            
        for i, message in enumerate(suite, start=1):
            msg_id = message.get("message_id", f"TEST-{i}")
            print(f"\n{'━' * 70}")
            print(f" EXECUTION: {msg_id}")
            print(f"{'━' * 70}\n")
            
            print(run_pipeline(message))
            print(f"\n{'─' * 70}")
            
    except json.JSONDecodeError:
        print(f"ERROR: Suite file '{suite_path}' contains invalid JSON.")

if __name__ == "__main__":
    main()