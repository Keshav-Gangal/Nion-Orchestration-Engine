"""
Module 1: AgentRegistry
Defines the complete Nion agent hierarchy, visibility rules,
and message-aware L3 output simulators.
Supports dynamic gap detection for all standard test cases.
"""

from dataclasses import dataclass
from typing import Optional
import random


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class AgentDef:
    name: str
    layer: str          # "L2" | "L3" | "CROSS_CUTTING"
    domain: Optional[str]   # L2 domain this agent belongs to (None for L2/cross-cutting)
    purpose: str


# ─────────────────────────────────────────────
# REGISTRY
# ─────────────────────────────────────────────

class AgentRegistry:
    """
    Single source of truth for all agents.
    Enforces visibility rules:
      - L1 can only delegate to: L2 domains + Cross-Cutting L3 agents
      - Each L2 can only route to: its own L3 agents + Cross-Cutting agents
    """

    # ── L2 Domain coordinators ──────────────────
    L2_DOMAINS = {
        "TRACKING_EXECUTION": AgentDef(
            name="TRACKING_EXECUTION",
            layer="L2",
            domain=None,
            purpose="Extract action items from customer request"
        ),
        "COMMUNICATION_COLLABORATION": AgentDef(
            name="COMMUNICATION_COLLABORATION",
            layer="L2",
            domain=None,
            purpose="Q&A, reporting, delivery"
        ),
        "LEARNING_IMPROVEMENT": AgentDef(
            name="LEARNING_IMPROVEMENT",
            layer="L2",
            domain=None,
            purpose="Learning from instructions"
        ),
    }

    # ── Cross-Cutting L3 agents ────────────
    CROSS_CUTTING = {
        "knowledge_retrieval": AgentDef(
            name="knowledge_retrieval",
            layer="CROSS_CUTTING",
            domain=None,
            purpose="Retrieve project context and timeline"
        ),
        "evaluation": AgentDef(
            name="evaluation",
            layer="CROSS_CUTTING",
            domain=None,
            purpose="Evaluate response before sending"
        ),
    }

    # ── L3 agents by L2 domain ──────────────
    L3_BY_DOMAIN = {
        "TRACKING_EXECUTION": {
            "action_item_extraction": AgentDef(
                name="action_item_extraction", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Extracts action items from message content, infers owners and due dates"
            ),
            "action_item_validation": AgentDef(
                name="action_item_validation", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Validates action items have required fields, flags missing info"
            ),
            "action_item_tracking": AgentDef(
                name="action_item_tracking", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Tracks action items to completion, provides status snapshots"
            ),
            "risk_extraction": AgentDef(
                name="risk_extraction", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Extracts risks from message content, assesses likelihood and impact"
            ),
            "risk_tracking": AgentDef(
                name="risk_tracking", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Tracks risks, provides risk snapshots"
            ),
            "issue_extraction": AgentDef(
                name="issue_extraction", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Extracts issues/problems from message content, assesses severity"
            ),
            "issue_tracking": AgentDef(
                name="issue_tracking", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Tracks issues to resolution, provides issue snapshots"
            ),
            "decision_extraction": AgentDef(
                name="decision_extraction", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Extracts decisions from message content, identifies decision maker"
            ),
            "decision_tracking": AgentDef(
                name="decision_tracking", layer="L3", domain="TRACKING_EXECUTION",
                purpose="Tracks decisions to implementation"
            ),
        },
        "COMMUNICATION_COLLABORATION": {
            "qna": AgentDef(
                name="qna", layer="L3", domain="COMMUNICATION_COLLABORATION",
                purpose="Formulates responses to questions, handles both direct answers and gap-aware responses"
            ),
            "report_generation": AgentDef(
                name="report_generation", layer="L3", domain="COMMUNICATION_COLLABORATION",
                purpose="Creates formatted reports (status reports, summaries, digests)"
            ),
            "message_delivery": AgentDef(
                name="message_delivery", layer="L3", domain="COMMUNICATION_COLLABORATION",
                purpose="Sends messages via appropriate channels (email, Slack, Teams)"
            ),
            "meeting_attendance": AgentDef(
                name="meeting_attendance", layer="L3", domain="COMMUNICATION_COLLABORATION",
                purpose="Captures meeting transcripts, generates meeting minutes"
            ),
        },
        "LEARNING_IMPROVEMENT": {
            "instruction_led_learning": AgentDef(
                name="instruction_led_learning", layer="L3", domain="LEARNING_IMPROVEMENT",
                purpose="Learns from explicit instructions, stores SOPs and rules"
            ),
        },
    }

    @classmethod
    def l1_can_delegate_to(cls, target: str) -> bool:
        return target in cls.L2_DOMAINS or target in cls.CROSS_CUTTING

    @classmethod
    def l2_can_route_to(cls, domain: str, agent: str) -> bool:
        own_agents = cls.L3_BY_DOMAIN.get(domain, {})
        return agent in own_agents or agent in cls.CROSS_CUTTING

    @staticmethod
    def simulate_l3_output(agent_name: str, message: dict) -> list[str]:
        sim = _L3Simulator(message)
        return sim.output_for(agent_name)


# ─────────────────────────────────────────────
# INTERNAL SIMULATOR HELPER
# ─────────────────────────────────────────────

class _L3Simulator:
    def __init__(self, message: dict):
        self.content     = message.get("content", "")
        self.project     = message.get("project") or "UNKNOWN"
        self.sender_name = message.get("sender", {}).get("name", "Unknown")
        self.source      = message.get("source", "unknown")
        
        topic_words = self.content.split()[:16]
        self.topic = " ".join(topic_words).rstrip("?,.")
        
        random.seed(hash(self.content[:40]))

    def output_for(self, agent_name: str) -> list[str]:
        dispatch = {
            "action_item_extraction":   self._action_item_extraction,
            "action_item_validation":   self._action_item_validation,
            "action_item_tracking":     self._action_item_tracking,
            "risk_extraction":          self._risk_extraction,
            "risk_tracking":            self._risk_tracking,
            "issue_extraction":         self._issue_extraction,
            "issue_tracking":           self._issue_tracking,
            "decision_extraction":      self._decision_extraction,
            "decision_tracking":        self._decision_tracking,
            "qna":                      self._qna,
            "report_generation":        self._report_generation,
            "message_delivery":         self._message_delivery,
            "meeting_attendance":       self._meeting_attendance,
            "knowledge_retrieval":      self._knowledge_retrieval,
            "evaluation":               self._evaluation,
            "instruction_led_learning": self._instruction_led_learning,
        }
        fn = dispatch.get(agent_name, self._generic)
        return fn()

    def _action_item_extraction(self):
        if "notifications" in self.content.lower() or "export" in self.content.lower():
            return [
                '• AI-001: "Evaluate real-time notifications feature"',
                '  Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]',
                '• AI-002: "Evaluate dashboard export feature"',
                '  Owner: ? | Due: ? | Flags: [MISSING_OWNER, MISSING_DUE_DATE]',
            ]
        elif "meeting" in self.source.lower():
            return [
                '• AI-001: "Fix staging environment (API Integration blocker)"',
                '  Owner: Dev | Due: ASAP | Flags: [URGENT]',
                '• AI-002: "Refactor auth module"',
                '  Owner: Tech Lead | Due: TBD | Flags: [PENDING_REVIEW]',
            ]
        return [
            f'• AI-001: "Assess requested changes in {self.project}"',
            '  Owner: ? | Due: ? | Flags: [MISSING_OWNER]',
            f'• AI-002: "Coordinate with {self.sender_name} on specifics"',
            f'  Owner: {self.sender_name} | Due: TBD'
        ]

    def _action_item_validation(self):
        return [
            "• Validation summary: 0/2 items fully valid",
            "• Missing Fields: Owner (AI-001), Due Date (AI-001, AI-002)",
            "• Status: VALIDATION_FAILED — Clarification Required"
        ]

    def _action_item_tracking(self):
        return [
            f"• Project: {self.project} | Status Snapshot",
            "• AI-001: OPEN — awaiting assignment",
            "• AI-002: OPEN — awaiting timeline"
        ]

    def _risk_extraction(self):
        if "timeline" in self.content.lower() or "add" in self.content.lower():
            return [
                '• RISK-001: "Timeline risk: Adding new scope to current sprint"',
                '  Likelihood: HIGH | Impact: HIGH',
                '• RISK-002: "Scope creep risk for project revenue target"',
                '  Likelihood: MEDIUM | Impact: MEDIUM',
            ]
        return [
            f'• RISK-001: "Unclear requirements for {self.topic}"',
            '  Likelihood: MEDIUM | Impact: HIGH',
            '• RISK-002: "Resource contention during code freeze"',
            '  Likelihood: LOW | Impact: MEDIUM'
        ]

    def _risk_tracking(self):
        return [
            f"• Project: {self.project} | Active Risks: 2 | Open: 2",
            "• RISK-001: OPEN — no mitigation plan assigned",
            "• RISK-002: OPEN — owner TBD"
        ]

    def _issue_extraction(self):
        if "meeting" in self.source.lower() or "blocked" in self.content.lower():
            return [
                '• ISSUE-001: "Staging environment down, API integration blocked"',
                '  Severity: CRITICAL | Status: OPEN',
                '• ISSUE-002: "3 critical bugs in payment flow"',
                '  Severity: CRITICAL | Status: OPEN',
            ]
        return [
            f'• ISSUE-001: "{self.topic}"',
            f'  Severity: MEDIUM | Reported by: {self.sender_name} | Status: OPEN'
        ]

    def _issue_tracking(self):
        return [
            f"• Project: {self.project} | Open Issues: 2 | Resolved: 0",
            "• ISSUE-001: OPEN — assigned to triage",
            "• ISSUE-002: OPEN — pending analysis"
        ]

    def _decision_extraction(self):
        if "should we" in self.content.lower() or "prioritize" in self.content.lower():
            return [
                '• DEC-001: "Prioritize security fixes over dashboard export"',
                f'  Decision Maker: {self.sender_name} | Status: PENDING'
            ]
        return [
            '• DEC-001: "Accept or reject customer feature request"',
            '  Decision Maker: Leadership | Status: PENDING'
        ]

    def _decision_tracking(self):
        return [
            f"• Project: {self.project} | Decisions Pending: 1",
            "• DEC-001: PENDING — awaiting sign-off"
        ]

    def _qna(self):
        # Case 6: Ambiguous Request (Missing Project ID)
        if self.project == "UNKNOWN" or not self.project:
            return [
                f'Response: "I\'ve received your request to \'{self.topic}\', but I need context."',
                '',
                'WHAT I NEED:',
                '• Project ID: I don\'t have a project context for this message.',
                '• Specifics: Please clarify which timeline or team you are referring to.',
                '',
                'I cannot extract action items or risks without a valid Project ID.'
            ]

        # Case 5: Urgent Escalation (Legal/Threats)
        if "legal" in self.content.lower() or "threaten" in self.content.lower():
            return [
                f'Response: "I have flagged the escalation for {self.project} as CRITICAL."',
                '',
                'WHAT I KNOW:',
                '• The client is threatening to escalate to legal.',
                '• Feature delivery promised for Q3 is still PENDING.',
                '',
                "WHAT I'VE LOGGED:",
                '• RISK-001: Legal escalation and client dissatisfaction.',
                '• ISSUE-001: Non-delivery of committed scope.',
                '',
                'WHAT I NEED:',
                '• Immediate context from the Engineering Lead (David Park) regarding the delay.',
                '• I am preparing a historical timeline for leadership review.'
            ]

        # Case 4: Meeting Transcript
        if "meeting" in self.source.lower():
            return [
                f'Response: "Meeting minutes and action items have been generated for {self.project}."',
                '',
                'SUMMARY OF DISCUSSED ITEMS:',
                '• API Integration: Blocked (Staging is down)',
                '• Payment Flow: 3 critical bugs found by QA',
                '• Technical: Potential auth module refactor',
                '',
                'NEXT STEPS:',
                '• Issues and Action Items have been logged in the tracking system.',
                '• Engineering and QA are notified of the current blockers.'
            ]

        # Case 1: Simple Status Question
        if "status" in self.content.lower():
            return [
                f'Response: "I have retrieved the latest updates for {self.project}."',
                '',
                'WHAT I KNOW:',
                f'• Project: {self.project}',
                '• Current Progress: 70% complete',
                '• Team Capacity: 85% utilized',
                '',
                "WHAT I'VE LOGGED:",
                '• Status request logged from Engineering Management.',
                '',
                'WHAT I NEED:',
                '• No further information required at this time.'
            ]

        # Case 3: Decision/Recommendation
        if "should we" in self.content.lower() or "prioritize" in self.content.lower():
            return [
                f'Response: "Regarding the prioritization between security and the dashboard for {self.project}:"',
                '',
                'WHAT I KNOW:',
                '• Security vulnerabilities require immediate attention for compliance.',
                '• Dashboard progress is currently at 70%.',
                '',
                'WHAT I RECOMMEND:',
                '• Prioritize security fixes first to mitigate immediate risk.',
                '',
                'WHAT I NEED:',
                '• Final sign-off on the revised sprint priority from leadership.'
            ]
        
        # Case 2 & Default: Feasibility Gap Detection
        needs = []
        if "estimate" not in self.content.lower():
            needs.append("• Complexity estimates from Engineering (Alex Kim / David Park)")
        if "sign-off" not in self.content.lower() and "work" in self.content.lower():
            needs.append("• Go/no-go decision from leadership")

        return [
            'Response: "Great news on the demo! For the feature request:',
            '',
            'WHAT I KNOW:',
            '• Current timeline: Dec 15 (code freeze Dec 10)',
            '• Team capacity: 85% utilized',
            '• Progress: 70% complete',
            '',
            "WHAT I'VE LOGGED:",
            '• 2 action items | 2 risks | 1 pending decision',
            '',
            'WHAT I NEED:'
        ] + (needs if needs else ["• No further information required."]) + [
            '',
            'I cannot assess feasibility without Engineering input on',
            'whether 2 new features can fit in 20 days at 85% capacity."'
        ]

    def _report_generation(self):
        return [
            f"• Report generated for {self.project}",
            "• Sections: Summary | Action Items | Risks | Issues | Decisions",
            f"• Format: Markdown | Audience: {self.sender_name}",
            "• Status: DRAFT — ready for review"
        ]

    def _message_delivery(self):
        output = [f"Channel: {self.source}", f"Recipient: {self.sender_name}"]
        if self.project == "PRJ-ALPHA":
            output.append("CC: Alex Kim (Engineering Manager)")
        output.append("Delivery Status: SENT")
        return output

    def _meeting_attendance(self):
        return [
            f"• Meeting transcript captured from source: {self.source}",
            f"• Participants detected: {self.sender_name} + team",
            "• Key items flagged: action items, blockers, decisions"
        ]

    def _knowledge_retrieval(self):
        return [
            f'• Project: {self.project}',
            '• Current Release Date: Dec 15',
            '• Days Remaining: 20',
            '• Code Freeze: Dec 10',
            '• Progress: 70%',
            '• Team Capacity: 85% utilized',
            '• Engineering Manager: Alex Kim',
            '• Tech Lead: David Park',
        ]

    def _evaluation(self):
        return [
            "• Relevance: PASS",
            "• Accuracy: PASS",
            "• Tone: PASS",
            "• Gaps Acknowledged: PASS",
            "• Result: APPROVED"
        ]

    def _instruction_led_learning(self):
        return [
            f'• New instruction captured from {self.sender_name}',
            f'• Topic: "{self.topic}..."',
            '• Status: SOP Updated / Active'
        ]

    def _generic(self):
        return [
            f"• Task executed for project {self.project}",
            f"• Input processed from {self.sender_name} via {self.source}",
            "• Status: COMPLETED"
        ]