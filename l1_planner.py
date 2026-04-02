"""
Module 3: L1Planner
Takes an IntentResult and message to produce a dynamic, ordered task plan.
Enforces L1 visibility rules: L1 only delegates to L2 domains or Cross-Cutting agents.
"""

from dataclasses import dataclass, field
from intent_analyzer import IntentResult

# ─────────────────────────────────────────────
# TASK DATA DEFINITIONS
# ─────────────────────────────────────────────

@dataclass
class Task:
    task_id: str
    target: str
    purpose: str
    depends_on: list[str] = field(default_factory=list)
    is_cross_cutting: bool = False

    @property
    def display_target(self) -> str:
        """Formats the target for the high-fidelity orchestration map."""
        if self.is_cross_cutting:
            return f"L3:{self.target} (Cross-Cutting)"
        
        return f"L2:{self.target}"

@dataclass
class L1Plan:
    tasks: list[Task]
    intent: str
    gaps: list[str]
    entities: list[str]

# ─────────────────────────────────────────────
# COMPOSABLE TASK BUILDERS
# ─────────────────────────────────────────────

def _tracking_tasks(intent: IntentResult, message: dict) -> list[tuple]:
    """Generates L2:TRACKING_EXECUTION tasks in the required PDF sequence."""
    tasks = []
    content = (message.get("content") or "").lower()
    src = message.get("source", "")
    
    all_intents = {intent.primary_intent} | set(intent.secondary_intents)

    # 1. Action Items
    if any(i in ("FEATURE_REQUEST", "FEASIBILITY_QUESTION", "MEETING_TRANSCRIPT", "ESCALATION", "DECISION_REQUEST") for i in all_intents):
        tasks.append(("TRACKING_EXECUTION", "Extract action items from customer request", False))

    # 2. Risks
    if any(i in ("FEATURE_REQUEST", "FEASIBILITY_QUESTION", "ESCALATION", "MEETING_TRANSCRIPT", "DECISION_REQUEST") for i in all_intents):
        tasks.append(("TRACKING_EXECUTION", "Extract risks from scope change request", False))

    # 3. Decisions
    if any(i in ("DECISION_REQUEST", "FEASIBILITY_QUESTION") for i in all_intents) or "should we" in content:
        tasks.append(("TRACKING_EXECUTION", "Extract decision needed", False))

    # 4. Issues / Blockers
    if any(i in ("ESCALATION", "MEETING_TRANSCRIPT", "DECISION_REQUEST") for i in all_intents) or \
       any(kw in content for kw in ("blocked", "bug", "issue", "wall", "delay", "broken")):
        tasks.append(("TRACKING_EXECUTION", "Extract issues/blockers from message", False))

    # 5. Meeting capture 
    if "MEETING_TRANSCRIPT" in all_intents or src == "meeting":
        tasks.append(("COMMUNICATION_COLLABORATION", "Capture meeting transcript and generate minutes", False))

    return tasks

def _context_task() -> tuple:
    """Retrieves project context from the knowledge base."""
    return ("knowledge_retrieval", "Retrieve project context and timeline", True)

def _communication_tasks(intent: IntentResult, message: dict) -> list[tuple]:
    """Generates L2:COMMUNICATION_COLLABORATION tasks based on intent."""
    tasks = []
    all_intents = {intent.primary_intent} | set(intent.secondary_intents)

    if "STATUS_QUERY" in all_intents:
        tasks.append(("COMMUNICATION_COLLABORATION", "Formulate status response for requester", False))
    elif "DECISION_REQUEST" in all_intents:
        tasks.append(("COMMUNICATION_COLLABORATION", "Formulate recommendation response", False))
    elif "ESCALATION" in all_intents:
        tasks.append(("COMMUNICATION_COLLABORATION", "Formulate urgent escalation response with known facts", False))
    elif "AMBIGUOUS" in all_intents and len(all_intents) == 1:
        tasks.append(("COMMUNICATION_COLLABORATION", "Formulate clarification request — intent unclear", False))
    elif any(i in ("FEATURE_REQUEST", "FEASIBILITY_QUESTION") for i in all_intents):
        tasks.append(("COMMUNICATION_COLLABORATION", "Formulate gap-aware response", False))
    elif "MEETING_TRANSCRIPT" in all_intents:
        tasks.append(("COMMUNICATION_COLLABORATION", "Distribute meeting summary to stakeholders", False))
    else:
        tasks.append(("COMMUNICATION_COLLABORATION", "Formulate response to sender", False))

    return tasks

def _evaluation_task() -> tuple:
    """Validates the output quality before delivery."""
    return ("evaluation", "Evaluate response before sending", True)

def _delivery_task() -> tuple:
    """Final delivery via the appropriate channel."""
    return ("COMMUNICATION_COLLABORATION", "Send response to sender", False)

def _learning_task() -> tuple:
    """Stores explicit instructions as project rules/SOPs."""
    return ("LEARNING_IMPROVEMENT", "Store instruction as SOP / rule for future use", False)

# ─────────────────────────────────────────────
# PLANNER CLASS
# ─────────────────────────────────────────────

class L1Planner:

    @classmethod
    def plan(cls, intent: IntentResult, message: dict) -> L1Plan:
        """Main planning loop for L1 orchestration."""
        raw_tasks: list[tuple] = []

        # Phase 1: Extraction Logic
        if intent.needs_tracking or intent.primary_intent == "MEETING_TRANSCRIPT":
            raw_tasks.extend(_tracking_tasks(intent, message))

        # Phase 2: Context Retrieval
        raw_tasks.append(_context_task())

        # Phase 3: Response Formulation
        if intent.needs_communication:
            raw_tasks.extend(_communication_tasks(intent, message))

        # Phase 4: Output Validation
        raw_tasks.append(_evaluation_task())

        # Phase 5: Channel Delivery
        raw_tasks.append(_delivery_task())

        # Side Phase: SOP Learning
        if intent.needs_learning:
            raw_tasks.append(_learning_task())

        tasks = cls._assign_ids_and_deps(raw_tasks)
        
        return L1Plan(
             tasks=tasks, 
             intent=intent.primary_intent, 
             gaps=intent.gaps, 
             entities=intent.entities
        )

    @staticmethod
    def _assign_ids_and_deps(raw_tasks: list[tuple]) -> list[Task]:
        """Handles task numbering and enforces required dependency structures."""
        tasks: list[Task] = []
        context_ids: list[str] = []
        extraction_ids: list[str] = []
        comm_ids: list[str] = []
        eval_ids: list[str] = []

        for i, (target, purpose, is_cc) in enumerate(raw_tasks, start=1):
            tid = f"TASK-{i:03d}"
            deps: list[str] = []

            if is_cc and target == "knowledge_retrieval":
                context_ids.append(tid)

            elif is_cc and target == "evaluation":
                deps = comm_ids.copy()
                eval_ids.append(tid)

            elif target == "TRACKING_EXECUTION" or ("capture" in purpose.lower()):
                deps = context_ids.copy()
                extraction_ids.append(tid)

            elif target == "COMMUNICATION_COLLABORATION" and "capture" not in purpose.lower() and "send" not in purpose.lower():
                # Ensures all extraction and context tasks precede the response formulation
                deps = sorted(extraction_ids) + context_ids
                comm_ids.append(tid)

            elif target == "COMMUNICATION_COLLABORATION" and "send" in purpose.lower():
                deps = eval_ids.copy()

            tasks.append(Task(
                task_id=tid,
                target=target,
                purpose=purpose,
                depends_on=deps,
                is_cross_cutting=is_cc,
            ))

        return tasks