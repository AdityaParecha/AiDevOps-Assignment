"""
Guardrails System for AI DevOps Scaling Assistant
==================================================

Implements input, retrieval, and output guardrails to prevent:
1. Questions outside the application's intended scope (DevOps / Kubernetes scaling)
2. Adversarial prompt injections and jailbreaks
3. Harmful, malicious, or destructive command requests
4. Excessively long or malformed inputs (DoS prevention)
5. Hallucinated answers when sufficient context is not available
6. System prompt leakage and ungrounded / unsupported claims in output
"""

import re
import math
from typing import Dict, Any, List, Optional, Tuple


# ============================================================
# STANDARD CONSTANTS & REFUSALS
# ============================================================

STANDARD_KB_REFUSAL = "The provided knowledge base does not contain enough information."

OUT_OF_SCOPE_REFUSAL = (
    "I am your AI DevOps Scaling Assistant, specialized in Kubernetes autoscaling, "
    "scaling policies, and infrastructure reliability.\n\n"
    "Your question appears to be outside this domain. I can help you with:\n"
    "• Kubernetes Horizontal Pod Autoscaler (HPA) & metrics\n"
    "• Application scaling policies & traffic spike mitigation\n"
    "• Scaling incident analysis & bottleneck resolution\n\n"
    "Please ask any question related to Kubernetes scaling or infrastructure!"
)

SECURITY_VIOLATION_REFUSAL = (
    "⚠️ Security Policy Alert: Your input contains patterns associated with prompt injection or system override attempts. "
    "To ensure reliable and secure operation, this request cannot be executed."
)

HARMFUL_CONTENT_REFUSAL = (
    "⚠️ Safety Policy Alert: Destructive commands or security exploits (such as system wipes or cluster deletions) "
    "are restricted by the safety guardrail."
)

INPUT_LENGTH_REFUSAL = (
    "Please provide a concise technical query between 3 and 1000 characters. "
    "Excessively long or empty inputs are restricted to maintain system performance."
)


# ============================================================
# GUARDRAIL RESULT DATA STRUCTURE
# ============================================================

class GuardrailDecision:
    def __init__(
        self,
        passed: bool,
        guardrail_name: str,
        action: str,  # "ALLOW", "BLOCK", "MODIFY"
        reason: str,
        sanitized_content: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        self.passed = passed
        self.guardrail_name = guardrail_name
        self.action = action
        self.reason = reason
        self.sanitized_content = sanitized_content
        self.metrics = metrics or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "guardrail": self.guardrail_name,
            "action": self.action,
            "reason": self.reason,
            "sanitized_content": self.sanitized_content,
            "metrics": self.metrics
        }


# ============================================================
# 1. INPUT GUARDRAILS
# ============================================================

class InputGuardrail:
    """
    Validates user input before it reaches RAG retrieval or LLM generation.
    Checks:
      - Length and character constraints
      - Adversarial prompt injection / jailbreak patterns
      - Destructive / harmful commands
      - Domain scope alignment
    """

    MIN_LENGTH = 3
    MAX_LENGTH = 1000

    # Patterns indicating adversarial injection or jailbreaks
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)",
        r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
        r"(?i)forget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)",
        r"(?i)reveal\s+(the\s+|your\s+)?(system\s+prompt|initial\s+prompt|secret\s+instructions)",
        r"(?i)output\s+(the\s+|your\s+)?(system\s+prompt|initial\s+prompt)",
        r"(?i)what\s+are\s+your\s+(exact\s+)?(instructions|rules|system\s+prompt)",
        r"(?i)you\s+are\s+now\s+(in\s+)?(DAN|developer\s+mode|unrestricted|god\s+mode)",
        r"(?i)pretend\s+(you\s+are|to\s+be)\s+(an?\s+)?unrestricted",
        r"(?i)bypass\s+(all\s+)?(content\s+filters|safety\s+protocols|restrictions)",
        r"(?i)jailbreak",
        r"(?i)system\s+override",
        r"(?i)<\s*\|\s*im_start\s*\|\s*>system",
        r"(?i)\[\s*INST\s*\]\s*override",
    ]

    # Patterns indicating destructive shell or cluster commands
    HARMFUL_PATTERNS = [
        r"(?i)\brm\s+-rf\s+[/~]",
        r"(?i)\bmkfs\.",
        r"(?i)\bdd\s+if=/dev/(zero|urandom|null)\s+of=",
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # Fork bomb
        r"(?i)\bkubectl\s+delete\s+(all|namespaces?|nodes?|pods?\s+--all)\b",
        r"(?i)\bdrop\s+database\b",
        r"(?i)\bdrop\s+table\b",
        r"(?i)\bunion\s+select\b",
        r"(?i)chmod\s+-R\s+777\s+/",
        r"(?i)curl\s+[^\n|]+\|\s*(ba)?sh",
        r"(?i)wget\s+[^\n|]+\|\s*(ba)?sh",
    ]

    # Allowed DevOps Domain Keywords
    DEVOPS_KEYWORDS = {
        "kubernetes", "k8s", "hpa", "autoscaling", "autoscaler", "autoscale",
        "replica", "replicas", "pod", "pods", "node", "nodes", "cluster",
        "cpu", "memory", "utilization", "latency", "throughput", "traffic",
        "spike", "spikes", "scale-down", "scale-up", "scaling", "queue",
        "bottleneck", "metrics", "incident", "policy", "capacity",
        "horizontal", "reactive", "predictive", "pre-scaling", "fluctuation",
        "resource", "container", "deployment", "workload", "service", "load"
    }

    # Definitely Out-of-Scope Topic Keywords
    OUT_OF_SCOPE_KEYWORDS = {
        "recipe", "bake", "baking", "cake", "cook", "cooking", "chocolate", "pizza",
        "ingredient", "dessert", "cocktail", "tea", "coffee", "food", "dish", "meal",
        "movie", "actor", "actress", "cinema", "hollywood", "bollywood", "song", "lyrics", "music",
        "football", "soccer", "basketball", "nba", "cricket", "world cup", "tennis", "match",
        "dating", "romance", "horoscope", "astrology", "love", "friendship",
        "symptoms", "medication", "cure", "disease", "treatment", "doctor", "health", "diet", "gym", "workout",
        "poem", "poetry", "bedtime story", "fiction", "novel", "joke", "jokes", "riddle",
        "president", "election", "politics", "politician",
        "weather", "temperature", "climate", "geography", "history",
        "photosynthesis", "biology", "physics", "chemistry", "homework"
    }

    @classmethod
    def validate(cls, question: str) -> GuardrailDecision:
        """
        Executes all input checks in sequence.
        Returns GuardrailDecision.
        """
        if not question or not question.strip():
            return GuardrailDecision(
                passed=False,
                guardrail_name="InputSanityGuardrail",
                action="BLOCK",
                reason="Input cannot be empty or whitespace only.",
                sanitized_content=INPUT_LENGTH_REFUSAL
            )

        cleaned_text = question.strip()

        # 1. Length Check
        if len(cleaned_text) < cls.MIN_LENGTH:
            return GuardrailDecision(
                passed=False,
                guardrail_name="InputLengthGuardrail",
                action="BLOCK",
                reason=f"Input is too short ({len(cleaned_text)} chars). Minimum is {cls.MIN_LENGTH}.",
                sanitized_content=INPUT_LENGTH_REFUSAL,
                metrics={"char_length": len(cleaned_text)}
            )

        if len(cleaned_text) > cls.MAX_LENGTH:
            return GuardrailDecision(
                passed=False,
                guardrail_name="InputLengthGuardrail",
                action="BLOCK",
                reason=f"Input exceeds maximum allowed length ({len(cleaned_text)} > {cls.MAX_LENGTH} chars).",
                sanitized_content=INPUT_LENGTH_REFUSAL,
                metrics={"char_length": len(cleaned_text)}
            )

        # Repetition flood detection
        if re.search(r"(.)\1{29,}", cleaned_text):
            return GuardrailDecision(
                passed=False,
                guardrail_name="InputSanityGuardrail",
                action="BLOCK",
                reason="Input contains excessive character repetition / flood attack.",
                sanitized_content=INPUT_LENGTH_REFUSAL
            )

        # 2. Security Check (Prompt Injection / Jailbreak)
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, cleaned_text):
                return GuardrailDecision(
                    passed=False,
                    guardrail_name="InputSecurityGuardrail",
                    action="BLOCK",
                    reason=f"Adversarial prompt injection or jailbreak pattern detected matching '{pattern}'.",
                    sanitized_content=SECURITY_VIOLATION_REFUSAL,
                    metrics={"detected_pattern": pattern}
                )

        # 3. Harmful Content Check (Destructive commands / exploits)
        for pattern in cls.HARMFUL_PATTERNS:
            if re.search(pattern, cleaned_text):
                return GuardrailDecision(
                    passed=False,
                    guardrail_name="InputSafetyGuardrail",
                    action="BLOCK",
                    reason=f"Harmful or destructive command pattern detected matching '{pattern}'.",
                    sanitized_content=HARMFUL_CONTENT_REFUSAL,
                    metrics={"detected_pattern": pattern}
                )

        # 4. Domain Scope Check
        lower_q = cleaned_text.lower()
        words = set(re.findall(r"\b[a-z0-9_-]+\b", lower_q))

        out_matches = set(words.intersection(cls.OUT_OF_SCOPE_KEYWORDS))
        for phrase in ["prime minister", "capital of", "how to make", "recipe for", "tell me a joke", "who is the", "who was"]:
            if phrase in lower_q:
                out_matches.add(phrase)

        devops_matches = words.intersection(cls.DEVOPS_KEYWORDS)
        has_devops_keyword = bool(devops_matches) or any(kw in lower_q for kw in cls.DEVOPS_KEYWORDS)

        # 4a. Explicit out-of-scope trigger
        if out_matches and not has_devops_keyword:
            return GuardrailDecision(
                passed=False,
                guardrail_name="InputScopeGuardrail",
                action="BLOCK",
                reason=f"Query is out-of-scope (detected off-topic terms: {list(out_matches)}).",
                sanitized_content=OUT_OF_SCOPE_REFUSAL,
                metrics={"out_of_scope_matches": list(out_matches)}
            )

        # 4b. General non-technical questions without any DevOps/infrastructure context
        if not has_devops_keyword and len(cleaned_text) > 10:
            system_terms = {"server", "database", "network", "system", "infrastructure", "devops", "cloud", "docker", "api", "cluster", "scaling", "latency"}
            if not words.intersection(system_terms):
                return GuardrailDecision(
                    passed=False,
                    guardrail_name="InputScopeGuardrail",
                    action="BLOCK",
                    reason="Query does not relate to DevOps, Kubernetes, or cloud infrastructure scaling.",
                    sanitized_content=OUT_OF_SCOPE_REFUSAL,
                    metrics={"no_devops_keywords": True}
                )

        # All input checks passed
        return GuardrailDecision(
            passed=True,
            guardrail_name="InputGuardrail",
            action="ALLOW",
            reason="Input passed all length, security, safety, and domain scope validations.",
            sanitized_content=cleaned_text,
            metrics={"char_length": len(cleaned_text), "devops_matches": list(devops_matches)}
        )


# ============================================================
# 2. RETRIEVAL GUARDRAILS
# ============================================================

class RetrievalGuardrail:
    """
    Validates the retrieved context from the vector database.
    Prevents the LLM from answering when sufficient information is not available.
    Checks:
      - Empty context
      - High vector distance (low semantic similarity)
      - Missing answers for specific unanswerable entity requests
    """

    # Maximum allowable vector distance (cosine / L2 in ChromaDB)
    # Beyond this threshold, retrieved chunks are considered irrelevant noise
    DISTANCE_THRESHOLD = 1.15

    # Specific unanswerable patterns not present in the DevOps knowledge base
    UNANSWERABLE_PATTERNS = [
        (r"(?i)exact\s+kubernetes\s+version", "Kubernetes version"),
        (r"(?i)exact\s+memory\s+limit", "memory limit"),
        (r"(?i)which\s+cloud\s+provider", "cloud provider"),
        (r"(?i)database\s+engine", "database engine"),
        (r"(?i)system\s+administrator(\s+name)?", "system administrator name"),
        (r"(?i)admin('s)?\s+(name|phone|email|contact)", "admin contact"),
        (r"(?i)root\s+password", "passwords/credentials"),
    ]

    @classmethod
    def validate(
        cls,
        question: str,
        context: str,
        distances: List[float],
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> GuardrailDecision:
        """
        Validates whether the retrieved context contains sufficient, relevant information.
        """
        # 1. Empty Context Check
        if not context or not context.strip():
            return GuardrailDecision(
                passed=False,
                guardrail_name="RetrievalSufficiencyGuardrail",
                action="BLOCK",
                reason="Retrieved knowledge base context is completely empty.",
                sanitized_content=STANDARD_KB_REFUSAL,
                metrics={"min_distance": None, "context_length": 0}
            )

        min_distance = min(distances) if distances else 999.0

        # 2. Distance / Relevance Threshold Check
        if min_distance > cls.DISTANCE_THRESHOLD:
            return GuardrailDecision(
                passed=False,
                guardrail_name="RetrievalRelevanceGuardrail",
                action="BLOCK",
                reason=f"Retrieved context has poor relevance (min distance {min_distance:.4f} > {cls.DISTANCE_THRESHOLD}).",
                sanitized_content=STANDARD_KB_REFUSAL,
                metrics={"min_distance": min_distance, "threshold": cls.DISTANCE_THRESHOLD}
            )

        # 3. Known Unanswerable Attribute Check
        # If the user asks for exact environment configurations not present in our knowledge base,
        # verify if the context actually contains the answer. If not, block before hallucination!
        for pattern, label in cls.UNANSWERABLE_PATTERNS:
            if re.search(pattern, question):
                # Check if the context contains specific factual answers
                # Our knowledge base only contains generic HPA concepts, not specific cluster specs
                if not cls._context_contains_unanswerable_facts(context, label):
                    return GuardrailDecision(
                        passed=False,
                        guardrail_name="RetrievalSufficiencyGuardrail",
                        action="BLOCK",
                        reason=f"The question asks for {label}, which is not documented in the knowledge base.",
                        sanitized_content=STANDARD_KB_REFUSAL,
                        metrics={"unanswerable_subject": label, "min_distance": min_distance}
                    )

        return GuardrailDecision(
            passed=True,
            guardrail_name="RetrievalGuardrail",
            action="ALLOW",
            reason="Retrieved context satisfies relevance and sufficiency criteria.",
            sanitized_content=context,
            metrics={"min_distance": min_distance, "context_length": len(context)}
        )

    @classmethod
    def _context_contains_unanswerable_facts(cls, context: str, label: str) -> bool:
        """Checks if specific factual configurations exist in the text."""
        context_lower = context.lower()
        if label == "Kubernetes version":
            return bool(re.search(r"\bv?1\.\d+(\.\d+)?\b", context_lower))
        if label == "memory limit":
            return bool(re.search(r"\b\d+\s*(mi|gi|mb|gb)\b", context_lower))
        if label == "cloud provider":
            return any(p in context_lower for p in ["aws", "azure", "gcp", "google cloud", "amazon web services"])
        if label == "database engine":
            return any(db in context_lower for db in ["postgres", "mysql", "mongodb", "redis", "oracle"])
        if "admin" in label:
            return "administrator:" in context_lower or "admin name" in context_lower
        return False


# ============================================================
# 3. OUTPUT GUARDRAILS
# ============================================================

class OutputGuardrail:
    """
    Validates and sanitizes LLM-generated output before returning it to the user.
    Checks:
      - Non-empty and reasonable output length
      - System prompt leakage
      - Hallucinated / unsupported factual claims (e.g. fake versions or credentials)
      - Consistent refusal formatting
    """

    SYSTEM_PROMPT_LEAK_PATTERNS = [
        r"(?i)you\s+are\s+an?\s+ai\s+devops\s+scaling\s+assistant",
        r"(?i)important\s+rules\s*:",
        r"(?i)use\s+the\s+context\s+as\s+the\s+primary\s+source\s+of\s+truth",
        r"(?i)do\s+not\s+invent\s+facts",
        r"(?i)knowledge\s+base\s+context\s*:",
        r"(?i)user\s+question\s*:",
    ]

    # Hallucinated specifics: if the model invents concrete cluster specs when not in context
    FABRICATED_SPECS = [
        r"(?i)\bKubernetes\s+(version\s+)?v?1\.\d{1,2}(\.\d+)?\b",
        r"(?i)\b(AWS|Amazon\s+Web\s+Services|Google\s+Cloud|GCP|Azure)\b",
        r"(?i)\b(PostgreSQL|MySQL|MongoDB|Redis|Oracle)\b",
        r"(?i)\b\d+\s*(GiB|MiB|GB|MB)\s+(RAM|memory)\s+limit\b",
    ]

    @classmethod
    def validate(
        cls,
        question: str,
        context: str,
        answer: str
    ) -> GuardrailDecision:
        """
        Validates LLM generation against output safety and faithfulness standards.
        """
        if not answer or not answer.strip():
            return GuardrailDecision(
                passed=False,
                guardrail_name="OutputSanityGuardrail",
                action="BLOCK",
                reason="LLM generated an empty response.",
                sanitized_content=STANDARD_KB_REFUSAL
            )

        cleaned_answer = answer.strip()

        # 1. System Prompt Leakage Check
        for pattern in cls.SYSTEM_PROMPT_LEAK_PATTERNS:
            if re.search(pattern, cleaned_answer):
                return GuardrailDecision(
                    passed=False,
                    guardrail_name="OutputPrivacyGuardrail",
                    action="MODIFY",
                    reason="Output contains leaked system prompt instructions.",
                    sanitized_content=cls._remove_prompt_leaks(cleaned_answer)
                )

        # 2. Unsupported Claim / Hallucination Check
        # If the question asks for something not in context, but the LLM invents a specific spec:
        for spec_pattern in cls.FABRICATED_SPECS:
            match = re.search(spec_pattern, cleaned_answer)
            if match:
                # Check if this exact spec exists in the retrieved context
                matched_text = match.group(0)
                if matched_text.lower() not in context.lower():
                    # The LLM hallucinated a specific technical detail not grounded in the KB!
                    return GuardrailDecision(
                        passed=False,
                        guardrail_name="OutputFaithfulnessGuardrail",
                        action="MODIFY",
                        reason=f"Output contains ungrounded hallucination: '{matched_text}' not in context.",
                        sanitized_content=STANDARD_KB_REFUSAL,
                        metrics={"hallucinated_claim": matched_text}
                    )

        # 3. Proper Refusal Enforcement
        # If the answer indicates lack of info, normalize to the standard clean refusal
        refusal_variants = [
            "the provided knowledge base does not contain enough information",
            "the knowledge base does not contain",
            "not mentioned in the provided context",
            "does not contain information about",
            "the context does not provide",
            "not enough information"
        ]
        if any(v in cleaned_answer.lower() for v in refusal_variants):
            return GuardrailDecision(
                passed=True,
                guardrail_name="OutputFormatGuardrail",
                action="ALLOW",
                reason="Output appropriately refuses with recognized refusal phrasing.",
                sanitized_content=STANDARD_KB_REFUSAL,
                metrics={"is_refusal": True}
            )

        return GuardrailDecision(
            passed=True,
            guardrail_name="OutputGuardrail",
            action="ALLOW",
            reason="Output passed all format, privacy, and grounding validations.",
            sanitized_content=cleaned_answer,
            metrics={"answer_length": len(cleaned_answer), "is_refusal": False}
        )

    @classmethod
    def _remove_prompt_leaks(cls, text: str) -> str:
        cleaned = text
        for pattern in cls.SYSTEM_PROMPT_LEAK_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned if len(cleaned) > 20 else STANDARD_KB_REFUSAL


# ============================================================
# UNIFIED GUARDRAILS ORCHESTRATOR
# ============================================================

class GuardrailsPipeline:
    """
    Coordinates the multi-stage guardrail evaluation:
      Stage 1: Input Guardrail
      Stage 2: Retrieval Guardrail
      Stage 3: Output Guardrail
    """

    @classmethod
    def process_input(cls, question: str) -> GuardrailDecision:
        return InputGuardrail.validate(question)

    @classmethod
    def process_retrieval(
        cls,
        question: str,
        context: str,
        distances: List[float],
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> GuardrailDecision:
        return RetrievalGuardrail.validate(question, context, distances, sources)

    @classmethod
    def process_output(
        cls,
        question: str,
        context: str,
        raw_answer: str
    ) -> GuardrailDecision:
        return OutputGuardrail.validate(question, context, raw_answer)
