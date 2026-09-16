"""
AI Output Testing Engine
========================

Treats LLM output as an untrusted candidate artifact that must satisfy
defined acceptance conditions before being delivered by the application.

Implements systematic tests for:
  1. Relevance: Is the answer relevant to the user question?
  2. Context Support (Faithfulness): Are claims supported by retrieved context?
  3. Hallucination Detection: Does the output contain unsupported claims?
  4. Format Compliance: Does the output adhere to length, privacy, and markdown rules?
  5. Sufficiency Answering: Does it answer when context is present?
  6. Appropriate Refusal: Does it refuse when information is absent or out-of-scope?

Defines explicit PASS / FAIL criteria and aggregates an overall ACCEPT / REJECT verdict.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set


STANDARD_REFUSAL = "The provided knowledge base does not contain enough information."

REFUSAL_INDICATORS = [
    "the provided knowledge base does not contain enough information",
    "does not contain enough information",
    "not mentioned in the provided context",
    "information is not available",
    "provided context does not contain",
    "not present in the context",
    "outside my operational scope",
    "outside this domain",
    "scaling assistant, specialized",
    "security guardrail triggered",
    "security policy alert",
    "safety policy alert",
    "safety guardrail triggered",
    "request rejected"
]

SYSTEM_PROMPT_LEAKS = [
    r"(?i)you\s+are\s+an?\s+ai\s+devops\s+scaling\s+assistant",
    r"(?i)important\s+rules\s*:",
    r"(?i)use\s+the\s+context\s+as\s+the\s+primary\s+source\s+of\s+truth",
    r"(?i)do\s+not\s+invent\s+facts",
    r"(?i)knowledge\s+base\s+context\s*:",
    r"(?i)user\s+question\s*:"
]

SPECIFIC_ENTITY_PATTERNS = [
    (r"\bv?1\.\d{1,2}(\.\d+)?\b", "version number"),
    (r"\b\d+\s*(gib|mib|gb|mb)\b", "memory specification"),
    (r"\b(aws|amazon\s+web\s+services|google\s+cloud|gcp|azure)\b", "cloud vendor"),
    (r"\b(postgresql|postgres|mysql|mongodb|redis|oracle)\b", "database system"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone number"),
]


class ConditionResult:
    def __init__(
        self,
        name: str,
        passed: bool,
        score: float,
        threshold: float,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.passed = passed
        self.score = score
        self.threshold = threshold
        self.reason = reason
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": round(self.score, 3),
            "threshold": self.threshold,
            "reason": self.reason,
            "details": self.details
        }


class AIOutputTester:
    """
    Automated test harness for evaluating candidate LLM output against
    predefined acceptance criteria.
    """

    # --------------------------------------------------------
    # 1. RELEVANCE TEST
    # --------------------------------------------------------
    @classmethod
    def test_relevance(cls, question: str, answer: str) -> ConditionResult:
        """
        Evaluates whether the candidate output is relevant to the question asked.
        Checks keyword overlap, semantic token presence, and refusal appropriateness.
        Criterion: relevance_score >= 0.50 (or valid refusal).
        """
        lower_q = question.lower()
        lower_a = answer.lower()

        # If it's a valid refusal, check if it's acknowledging absence
        is_refusal = any(ref in lower_a for ref in REFUSAL_INDICATORS)
        if is_refusal:
            return ConditionResult(
                name="Relevance",
                passed=True,
                score=1.0,
                threshold=0.50,
                reason="Output appropriately recognizes boundary / lack of info.",
                details={"is_refusal": True}
            )

        # Tokenize meaningful words (>2 chars, alphanumeric)
        q_words = set(re.findall(r"\b[a-z0-9_-]{3,}\b", lower_q))
        a_words = set(re.findall(r"\b[a-z0-9_-]{3,}\b", lower_a))

        # Filter common stopwords
        stopwords = {"what", "when", "where", "which", "why", "how", "the", "and", "for", "with", "does", "can"}
        q_clean = q_words - stopwords
        a_clean = a_words - stopwords

        if not q_clean:
            score = 1.0
        else:
            intersection = q_clean.intersection(a_clean)
            score = len(intersection) / len(q_clean)

        passed = (score >= 0.50) or (len(q_clean.intersection(a_clean)) >= 2)
        reason = f"Token overlap with question: {score:.1%} ({len(q_clean.intersection(a_clean))} matching terms)."

        return ConditionResult(
            name="Relevance",
            passed=passed,
            score=min(1.0, score),
            threshold=0.50,
            reason=reason,
            details={"matching_terms": list(q_clean.intersection(a_clean))}
        )

    # --------------------------------------------------------
    # 2. CONTEXT SUPPORT TEST (Faithfulness / Groundedness)
    # --------------------------------------------------------
    @classmethod
    def test_context_support(cls, context: str, answer: str) -> ConditionResult:
        """
        Evaluates whether factual claims in the answer are grounded in the retrieved context.
        Criterion: groundedness_score >= 0.70.
        """
        lower_a = answer.lower()
        lower_c = context.lower()

        # If it is a refusal, it is grounded in the lack of context
        if any(ref in lower_a for ref in REFUSAL_INDICATORS):
            return ConditionResult(
                name="ContextSupport",
                passed=True,
                score=1.0,
                threshold=0.70,
                reason="Valid refusal correctly reflects lack of context.",
                details={"is_refusal": True}
            )

        if not context.strip():
            # If context is empty but answer is non-empty, it's 0% supported!
            return ConditionResult(
                name="ContextSupport",
                passed=False,
                score=0.0,
                threshold=0.70,
                reason="Context was empty but model generated ungrounded assertions.",
                details={"context_empty": True}
            )

        # Break answer into sentences
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", answer) if len(s.strip()) > 15]
        if not sentences:
            return ConditionResult(
                name="ContextSupport",
                passed=False,
                score=0.0,
                threshold=0.70,
                reason="Answer too brief or malformed to extract claims."
            )

        grounded_count = 0
        context_words = set(re.findall(r"\b[a-z0-9_-]{3,}\b", lower_c))

        for sent in sentences:
            sent_words = set(re.findall(r"\b[a-z0-9_-]{3,}\b", sent.lower()))
            if not sent_words:
                continue
            overlap = sent_words.intersection(context_words)
            overlap_ratio = len(overlap) / len(sent_words)
            # If >= 50% of the sentence's substantive vocabulary appears in context
            if overlap_ratio >= 0.50:
                grounded_count += 1

        score = grounded_count / len(sentences) if sentences else 0.0
        passed = score >= 0.70

        reason = f"{grounded_count}/{len(sentences)} sentences ({score:.1%}) grounded in retrieved context."
        return ConditionResult(
            name="ContextSupport",
            passed=passed,
            score=score,
            threshold=0.70,
            reason=reason,
            details={"grounded_sentences": grounded_count, "total_sentences": len(sentences)}
        )

    # --------------------------------------------------------
    # 3. UNSUPPORTED CLAIMS / HALLUCINATION TEST
    # --------------------------------------------------------
    @classmethod
    def test_unsupported_claims(cls, context: str, answer: str) -> ConditionResult:
        """
        Scans for specific named entities, versions, memory quantities, or credentials
        in the answer that do NOT appear anywhere in the retrieved context.
        Criterion: unsupported_claims_count == 0.
        """
        lower_a = answer.lower()
        lower_c = context.lower()

        # If standard refusal, no claims made
        if any(ref in lower_a for ref in REFUSAL_INDICATORS):
            return ConditionResult(
                name="UnsupportedClaims",
                passed=True,
                score=1.0,
                threshold=1.0,
                reason="No unsupported claims; output is a clean refusal.",
                details={"unsupported_claims": []}
            )

        unsupported_claims: List[Dict[str, str]] = []

        for pattern, claim_type in SPECIFIC_ENTITY_PATTERNS:
            matches = re.finditer(pattern, lower_a)
            for m in matches:
                entity = m.group(0)
                # Check if entity is present in context
                if entity not in lower_c:
                    unsupported_claims.append({
                        "entity": entity,
                        "type": claim_type
                    })

        passed = len(unsupported_claims) == 0
        score = 1.0 if passed else 0.0
        reason = (
            "Zero unsupported technical claims detected."
            if passed
            else f"Detected {len(unsupported_claims)} unsupported claims not present in context: {unsupported_claims}"
        )

        return ConditionResult(
            name="UnsupportedClaims",
            passed=passed,
            score=score,
            threshold=1.0,
            reason=reason,
            details={"unsupported_claims": unsupported_claims}
        )

    # --------------------------------------------------------
    # 4. FORMAT COMPLIANCE TEST
    # --------------------------------------------------------
    @classmethod
    def test_format_compliance(cls, answer: str) -> ConditionResult:
        """
        Evaluates structural formatting, length bounds, and system prompt leakage.
        Criterion: non-empty, 15 <= len <= 2500, no prompt leakage.
        """
        if not answer or not answer.strip():
            return ConditionResult(
                name="FormatCompliance",
                passed=False,
                score=0.0,
                threshold=1.0,
                reason="Output is completely empty."
            )

        clean = answer.strip()
        length = len(clean)

        if length < 15:
            return ConditionResult(
                name="FormatCompliance",
                passed=False,
                score=0.0,
                threshold=1.0,
                reason=f"Output is too short ({length} characters < 15).",
                details={"length": length}
            )

        if length > 2500:
            return ConditionResult(
                name="FormatCompliance",
                passed=False,
                score=0.0,
                threshold=1.0,
                reason=f"Output exceeds allowable response size ({length} > 2500 chars).",
                details={"length": length}
            )

        # Check prompt leaks
        for leak_pattern in SYSTEM_PROMPT_LEAKS:
            if re.search(leak_pattern, clean):
                return ConditionResult(
                    name="FormatCompliance",
                    passed=False,
                    score=0.0,
                    threshold=1.0,
                    reason=f"Output contains leaked system prompt instructions matching '{leak_pattern}'.",
                    details={"leak_pattern": leak_pattern}
                )

        return ConditionResult(
            name="FormatCompliance",
            passed=True,
            score=1.0,
            threshold=1.0,
            reason=f"Format compliance satisfied (length: {length} chars, no prompt leakage).",
            details={"length": length}
        )

    # --------------------------------------------------------
    # 5. SUFFICIENCY ANSWER TEST
    # --------------------------------------------------------
    @classmethod
    def test_sufficiency_answer(
        cls,
        category: str,
        answer: str,
        context_available: bool
    ) -> ConditionResult:
        """
        Checks if the LLM provided an informative technical answer when sufficient
        information exists (i.e. does not falsely refuse).
        Criterion: If category is in-scope and context exists, output must NOT be a refusal.
        """
        lower_a = answer.lower()
        is_refusal = any(ref in lower_a for ref in REFUSAL_INDICATORS)

        if category in ["basic", "incident", "policy", "comparison", "in_scope_valid"]:
            if context_available:
                if is_refusal:
                    return ConditionResult(
                        name="SufficiencyAnswer",
                        passed=False,
                        score=0.0,
                        threshold=1.0,
                        reason="False Refusal: Context was available but model refused to answer.",
                        details={"category": category, "is_refusal": True}
                    )
                else:
                    return ConditionResult(
                        name="SufficiencyAnswer",
                        passed=True,
                        score=1.0,
                        threshold=1.0,
                        reason="Substantive technical answer provided for documented topic.",
                        details={"category": category}
                    )

        # For unanswerable or out of scope, this test trivially passes
        return ConditionResult(
            name="SufficiencyAnswer",
            passed=True,
            score=1.0,
            threshold=1.0,
            reason="Not applicable to unanswerable / out-of-scope query (pass by default).",
            details={"category": category}
        )

    # --------------------------------------------------------
    # 6. APPROPRIATE REFUSAL TEST
    # --------------------------------------------------------
    @classmethod
    def test_appropriate_refusal(
        cls,
        category: str,
        answer: str,
        context_available: bool
    ) -> ConditionResult:
        """
        Checks if the LLM appropriately refused when information is unavailable or out-of-scope.
        Criterion: If category is unanswerable, out_of_scope, or context is missing,
                   output MUST be an explicit refusal.
        """
        lower_a = answer.lower()
        is_refusal = any(ref in lower_a for ref in REFUSAL_INDICATORS)

        is_unanswerable = category in ["unanswerable", "unanswerable_domain", "out_of_scope"]

        if is_unanswerable or not context_available:
            if is_refusal:
                return ConditionResult(
                    name="AppropriateRefusal",
                    passed=True,
                    score=1.0,
                    threshold=1.0,
                    reason="Model appropriately refused when information is unavailable or out-of-scope.",
                    details={"category": category, "is_refusal": True}
                )
            else:
                return ConditionResult(
                    name="AppropriateRefusal",
                    passed=False,
                    score=0.0,
                    threshold=1.0,
                    reason="Failure to Refuse: Model attempted to answer an unanswerable or out-of-scope query.",
                    details={"category": category, "is_refusal": False}
                )

        # In-scope answerable questions do not require refusal
        return ConditionResult(
            name="AppropriateRefusal",
            passed=True,
            score=1.0,
            threshold=1.0,
            reason="Not applicable for valid in-scope query with context (pass by default).",
            details={"category": category}
        )

    # --------------------------------------------------------
    # AGGREGATE EVALUATION
    # --------------------------------------------------------
    @classmethod
    def evaluate_output(
        cls,
        question: str,
        category: str,
        context: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Executes all 6 output tests, determines individual pass/fail,
        and computes the overall ACCEPT / REJECT verdict.
        """
        has_context = bool(context and len(context.strip()) > 50)

        # Run all 6 condition tests
        relevance_res = cls.test_relevance(question, answer)
        context_res = cls.test_context_support(context, answer)
        claims_res = cls.test_unsupported_claims(context, answer)
        format_res = cls.test_format_compliance(answer)
        sufficiency_res = cls.test_sufficiency_answer(category, answer, has_context)
        refusal_res = cls.test_appropriate_refusal(category, answer, has_context)

        conditions = [
            relevance_res,
            context_res,
            claims_res,
            format_res,
            sufficiency_res,
            refusal_res
        ]

        failed_conditions = [c.name for c in conditions if not c.passed]
        overall_verdict = "ACCEPTED" if len(failed_conditions) == 0 else "REJECTED"

        return {
            "overall_verdict": overall_verdict,
            "passed_all": len(failed_conditions) == 0,
            "failed_conditions": failed_conditions,
            "conditions": {c.name: c.to_dict() for c in conditions},
            "summary": {
                "total_conditions": len(conditions),
                "passed_conditions": len(conditions) - len(failed_conditions),
                "acceptance_rate_pct": round(((len(conditions) - len(failed_conditions)) / len(conditions)) * 100, 1)
            }
        }
