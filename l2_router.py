"""
Module 4: L2Router
For each L2-targeted task in the plan, selects the correct L3 agent(s)
within that domain while enforcing strict L2 visibility rules.
"""

from dataclasses import dataclass
from agent_registery import AgentRegistry
from l1_planner import Task


# ─────────────────────────────────────────────
# ROUTED TASK DATA DEFINITION
# ─────────────────────────────────────────────

@dataclass
class RoutedTask:
    parent_task: Task
    l3_agents: list[str]          # Ordered list of L3 agent names to invoke


# ─────────────────────────────────────────────
# ROUTING STRATEGIES
# ─────────────────────────────────────────────

# Maps domain-specific keywords to L3 agents.
# First match wins based on the lower-cased purpose string.

_TRACKING_ROUTES: list[tuple[str, list[str]]] = [
    ("extract action item",         ["action_item_extraction"]),
    ("extract decision",            ["decision_extraction"]),
    ("extract risk",                ["risk_extraction"]),
    ("extract issue",               ["issue_extraction"]),
    ("track action",                ["action_item_tracking"]),
    ("track risk",                  ["risk_tracking"]),
    ("track issue",                 ["issue_tracking"]),
    ("track decision",              ["decision_tracking"]),
    ("validate action",             ["action_item_validation"]),
]

_COMMS_ROUTES: list[tuple[str, list[str]]] = [
    ("capture meeting",             ["meeting_attendance"]),
    ("generate meeting",            ["meeting_attendance"]),
    ("status report",               ["report_generation"]),
    ("generate status",             ["report_generation"]),
    ("gap-aware",                   ["qna"]),
    ("feasibility",                 ["qna"]),
    ("recommendation",              ["qna"]),
    ("clarification",               ["qna"]),
    ("formulate",                   ["qna"]),
    ("distribute",                  ["message_delivery"]),
    ("send",                        ["message_delivery"]),
    ("deliver",                     ["message_delivery"]),
    ("urgent",                      ["qna"]),
    ("escalation",                  ["qna"]),
]

_LEARNING_ROUTES: list[tuple[str, list[str]]] = [
    ("store",                       ["instruction_led_learning"]),
    ("instruction",                 ["instruction_led_learning"]),
    ("sop",                         ["instruction_led_learning"]),
    ("learn",                       ["instruction_led_learning"]),
]

_DOMAIN_ROUTES = {
    "TRACKING_EXECUTION":          _TRACKING_ROUTES,
    "COMMUNICATION_COLLABORATION": _COMMS_ROUTES,
    "LEARNING_IMPROVEMENT":        _LEARNING_ROUTES,
}

_DOMAIN_FALLBACK = {
    "TRACKING_EXECUTION":          ["action_item_extraction"],
    "COMMUNICATION_COLLABORATION": ["qna"],
    "LEARNING_IMPROVEMENT":        ["instruction_led_learning"],
}


# ─────────────────────────────────────────────
# ROUTER CLASS
# ─────────────────────────────────────────────

class L2Router:

    @classmethod
    def route(cls, task: Task) -> RoutedTask:
        """
        Maps an L2-targeted Task to specific L3 agents.
        Cross-cutting tasks bypass sub-routing and execute directly.
        """
        if task.is_cross_cutting:
            return RoutedTask(parent_task=task, l3_agents=[task.target])

        domain = task.target
        routes = _DOMAIN_ROUTES.get(domain)
        
        if not routes:
            return RoutedTask(parent_task=task, l3_agents=[])

        purpose_lower = task.purpose.lower()
        
        for keyword, agents in routes:
            if keyword in purpose_lower:
                # Validation loop to enforce the L2 visibility rule
                valid = [a for a in agents
                         if AgentRegistry.l2_can_route_to(domain, a)]
                if valid:
                    return RoutedTask(parent_task=task, l3_agents=valid)

        # Fallback to domain default if no keywords match
        fallback = _DOMAIN_FALLBACK.get(domain, [])
        return RoutedTask(parent_task=task, l3_agents=fallback)

    @classmethod
    def route_all(cls, tasks: list[Task]) -> list[RoutedTask]:
        return [cls.route(t) for t in tasks]