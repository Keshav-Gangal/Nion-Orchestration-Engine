"""
Module 2: IntentAnalyzer
Score-based, extensible intent detection.
Processes message content to determine primary/secondary intents, 
extract entities, and identify information gaps.
"""

from dataclasses import dataclass, field
import re

# ─────────────────────────────────────────────
# RESULT TYPE
# ─────────────────────────────────────────────

@dataclass
class IntentResult:
    primary_intent: str          # e.g. "FEATURE_REQUEST"
    secondary_intents: list[str] # additional detected intents
    entities: list[str]          # key nouns extracted
    gaps: list[str]              # missing info detected
    confidence: float            # 0.0–1.0
    needs_tracking: bool         # should TRACKING_EXECUTION be involved?
    needs_communication: bool    # should COMMUNICATION_COLLABORATION be involved?
    needs_learning: bool         # should LEARNING_IMPROVEMENT be involved?
    is_ambiguous: bool
    raw_scores: dict = field(default_factory=dict)


# ─────────────────────────────────────────────
# PATTERN DEFINITIONS
# ─────────────────────────────────────────────

INTENT_PATTERNS = {
    "STATUS_QUERY": {
        "patterns": [
            r"what.?s the status",
            r"status (of|on|for)",
            r"progress (on|of|for|update)",
            r"any updates?",
            r"where (are|is) we",
            r"how (is|are).{0,20}going",
            r"update (me|us) on",
            r"timeline (for|of|on)",
            r"(is|are) (it|they|we) on track",
        ],
        "weight": 1.0,
        "priority": 3,
    },
    "FEATURE_REQUEST": {
        "patterns": [
            r"add (a |an )?(new )?feature",
            r"implement(ing)?",
            r"build (a|an|the)",
            r"(new|additional) (feature|functionality|capability)",
            r"they.?(want|need|asked|requesting).{0,30}(feature|add|implement)",
            r"willing to pay",
            r"(20|30|50)% more",
            r"(feature request|enhancement request)",
            r"we need to (add|implement|build|improve)",
        ],
        "weight": 1.2,
        "priority": 4,
    },
    "FEASIBILITY_QUESTION": {
        "patterns": [
            r"can we (make|do|fit|ship|deliver|add)",
            r"is it (possible|feasible|doable)",
            r"(fit|deliver|complete).{0,20}(timeline|deadline|schedule)",
            r"(capacity|bandwidth|resource)",
            r"make (this|it) work",
            r"(same|original|existing) timeline",
            r"(before|by|within).{0,25}(release|deadline|launch|go.live)",
        ],
        "weight": 1.1,
        "priority": 3,
    },
    "DECISION_REQUEST": {
        "patterns": [
            r"should we",
            r"(recommend|suggest|advise)",
            r"(approve|reject|accept|decline)",
            r"(prioritize|priority between|choose between)",
            r"(go|no.go) decision",
            r"what (do you think|would you recommend|should)",
            r"(which|what) (option|approach|path)",
        ],
        "weight": 1.0,
        "priority": 2,
    },
    "MEETING_TRANSCRIPT": {
        "patterns": [
            r"(Dev|QA|Designer|Tech Lead|PM|Manager)\s*:",
            r"(blocked|blocker) on",
            r"(found|discovered) \d+ (bug|issue|defect)",
            r"(ready|complete[d]?) by (thursday|friday|monday|eod|eow)",
            r"(refactor|rework|rewrite)",
            r"(staging|prod|production) is (down|broken|failing)",
        ],
        "weight": 1.2,
        "priority": 4,
    },
    "ESCALATION": {
        "patterns": [
            r"(urgent|urgently|asap|immediately)",
            r"(blocked|blocking|showstopper)",
            r"(threaten|legal|lawsuit|escalat)",
            r"(critical|severity.1|sev.1|p0|p1)",
            r"(promised|committed).{0,30}(not|still|yet)",
            r"(customer|client).{0,20}(angry|unhappy|frustrated|threaten)",
            r"what happened",
        ],
        "weight": 1.3,
        "priority": 5,
    },
    "INSTRUCTION": {
        "patterns": [
            r"(always|never|from now on|going forward)",
            r"(rule|policy|process|procedure|sop)",
            r"(remember|note that|make sure|ensure)",
            r"(learn|update your|store this|save this)",
            r"(whenever|every time).{0,30}(you|we|the system)",
        ],
        "weight": 0.7,
        "priority": 1,
    },
    "AMBIGUOUS": {
        "patterns": [
            r"^.{0,30}$",
            r"(speed|faster|quicker|better).{0,10}(up|things|it)",
            r"^(we need to|let.?s|maybe we should)\b",
        ],
        "weight": 0.4,
        "priority": 0,
    },
}

# Routing signals
TRACKING_INTENTS      = {
    "FEATURE_REQUEST", "MEETING_TRANSCRIPT", "ESCALATION", 
    "FEASIBILITY_QUESTION", "DECISION_REQUEST"
}

COMMUNICATION_INTENTS = {
    "STATUS_QUERY", "DECISION_REQUEST", "ESCALATION", 
    "FEATURE_REQUEST", "FEASIBILITY_QUESTION", "AMBIGUOUS",
    "INSTRUCTION"
}

LEARNING_INTENTS      = {"INSTRUCTION"}

THRESHOLD = 0.5


# ─────────────────────────────────────────────
# ENTITY EXTRACTOR PATTERNS
# ─────────────────────────────────────────────

ENTITY_PATTERNS = [
    r"\b(SSO|API|auth(?:entication)?|dashboard|notifications?|export|integration)\b",
    r"\b(security|bugs?|features?|refactor|payment|deploy)\b",
    r"\b(Q[1-4]|Dec(?:ember)?|Jan(?:uary)?|sprint\s*\d+)\b",
    r"\b(PRJ-[A-Z0-9]+)\b",
    r"\b(release|deadline|milestone|go.live)\b",
]

GAP_PATTERNS = {
    "MISSING_OWNER":    r"\?|\bunknown\b|\bwho\b|\bwhose\b",
    "MISSING_DUE_DATE": r"\bwhen\b|\btbd\b|\bno date\b",
    "MISSING_PROJECT":  r"project.*null|no project",
    "VAGUE_REQUEST":    r"^.{1,30}$",
    "MISSING_CONTEXT":  r"speed.*up|better|faster|what happened|unclear",
}


# ─────────────────────────────────────────────
# ANALYZER CLASS
# ─────────────────────────────────────────────

class IntentAnalyzer:

    @classmethod
    def analyze(cls, message: dict) -> IntentResult:
        content = message.get("content", "")
        project = message.get("project")

        scores = cls._score_intents(content)
        primary, secondary = cls._pick_intents(scores)
        entities = cls._extract_entities(content)
        gaps     = cls._detect_gaps(content, project, message)

        is_ambiguous = (
            primary == "AMBIGUOUS"
            or scores.get(primary, 0) < THRESHOLD
            or not content.strip()
        )

        needs_tracking      = primary in TRACKING_INTENTS or any(i in TRACKING_INTENTS for i in secondary)
        needs_communication = primary in COMMUNICATION_INTENTS or any(i in COMMUNICATION_INTENTS for i in secondary)
        needs_learning      = primary in LEARNING_INTENTS

        if is_ambiguous:
            needs_communication = True

        return IntentResult(
            primary_intent=primary,
            secondary_intents=secondary,
            entities=entities,
            gaps=gaps,
            confidence=round(scores.get(primary, 0.0), 2),
            needs_tracking=needs_tracking,
            needs_communication=needs_communication,
            needs_learning=needs_learning,
            is_ambiguous=is_ambiguous,
            raw_scores={k: round(v, 2) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
        )

    # ── Internal Scoring Logic ───────────────────────────────────────────

    @classmethod
    def _score_intents(cls, text: str) -> dict[str, float]:
        text_lower = text.lower()
        scores: dict[str, float] = {}

        for intent, cfg in INTENT_PATTERNS.items():
            total = 0.0
            for pat in cfg["patterns"]:
                matches = re.findall(pat, text_lower, re.IGNORECASE)
                total += len(matches) * cfg["weight"]
            if total > 0:
                scores[intent] = total

        return scores

    @classmethod
    def _pick_intents(cls, scores: dict[str, float]) -> tuple[str, list[str]]:
        if not scores:
            return "AMBIGUOUS", []

        ranked = sorted(
            scores.items(),
            key=lambda kv: (kv[1], INTENT_PATTERNS[kv[0]]["priority"]),
            reverse=True,
        )

        primary = ranked[0][0]
        secondary = [
            k for k, v in ranked[1:]
            if v >= THRESHOLD and k != "AMBIGUOUS"
        ]
        return primary, secondary

    # ── Entity / Gap Extraction ──────────────────────────────────────────

    @classmethod
    def _extract_entities(cls, text: str) -> list[str]:
        found = []
        for pat in ENTITY_PATTERNS:
            matches = re.findall(pat, text, re.IGNORECASE)
            found.extend(m if isinstance(m, str) else m[0] for m in matches)
        
        seen = set()
        return [x for x in found if not (x.lower() in seen or seen.add(x.lower()))]

    @classmethod
    def _detect_gaps(cls, text: str, project, message: dict) -> list[str]:
        gaps = []
        text_lower = text.lower()

        for gap_name, pat in GAP_PATTERNS.items():
            if re.search(pat, text_lower, re.IGNORECASE):
                gaps.append(gap_name)

        if not project:
            gaps.append("MISSING_PROJECT")

        sender = message.get("sender", {})
        if not sender.get("name") or sender.get("role", "").lower() in ("unknown", ""):
            gaps.append("UNKNOWN_SENDER")

        return list(dict.fromkeys(gaps))