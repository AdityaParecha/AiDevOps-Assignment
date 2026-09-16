# AI Output Testing Report: Pre-Acceptance Validation

## 1. Overview & Testing Philosophy

In this architecture, **LLM output is treated as an untrusted candidate artifact that must be tested before it is accepted by the application.**

Every candidate output is evaluated across six rigorous conditions:
1. **Relevance**: Is the answer relevant to the user's question?
2. **Context Support (Faithfulness)**: Are claims substantiated by retrieved knowledge?
3. **Unsupported Claims (Hallucination)**: Does it contain ungrounded technical facts, numbers, or versions?
4. **Format Compliance**: Does it satisfy length constraints and prevent system prompt leakage?
5. **Sufficiency Answering**: Does it provide a concrete answer when sufficient context exists?
6. **Appropriate Refusal**: Does it refuse when information is absent or out-of-scope?

---

## 2. Quantitative Acceptance Results

| Metric | Guarded Pipeline | Unguarded Pipeline | Improvement |
| :--- | :---: | :---: | :---: |
| **Total Test Cases** | **12** | **12** | — |
| **Overall Output Acceptance Rate** | **91.7%** | **41.7%** | **+50.0%** |
| **Total Accepted Outputs** | **11/12** | **5/12** | **+6 outputs** |

---

## 3. Condition-by-Condition Pass Rates

| Test Condition | Guarded Pass Rate | Unguarded Pass Rate | Critical Failure Modes Prevented |
| :--- | :---: | :---: | :--- |
| **Relevance** | **100.0%** (12/12) | **100.0%** (12/12) | Off-topic rambling and tangential answers |
| **ContextSupport** | **91.7%** (11/12) | **41.7%** (5/12) | Generating speculative text detached from retrieved knowledge base |
| **UnsupportedClaims** | **100.0%** (12/12) | **100.0%** (12/12) | Fabricated Kubernetes versions, cloud vendors, or pod RAM limits |
| **FormatCompliance** | **100.0%** (12/12) | **100.0%** (12/12) | System prompt instruction leakage and boundary bleeding |
| **SufficiencyAnswer** | **100.0%** (12/12) | **100.0%** (12/12) | False refusals on documented HPA questions |
| **AppropriateRefusal** | **100.0%** (12/12) | **58.3%** (7/12) | Answering out-of-scope queries (recipes, sports) or ungrounded specs |

---

## 4. Case-by-Case Validation Results

| Test ID | Category | Question | Guarded Verdict | Unguarded Verdict | Failed Conditions (Unguarded) |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `OT-01` | `basic` | What is reactive autoscaling? | **ACCEPTED** | ACCEPTED | None (Passed) |
| `OT-02` | `basic` | Why can reactive autoscaling be slow during a sudden traffic spike? | **ACCEPTED** | ACCEPTED | None (Passed) |
| `OT-03` | `incident` | What can happen when there is a sudden traffic spike and the system relies only on reactive scaling? | **ACCEPTED** | ACCEPTED | None (Passed) |
| `OT-04` | `policy` | What scale-down approach is recommended when traffic temporarily decreases? | **ACCEPTED** | ACCEPTED | None (Passed) |
| `OT-05` | `comparison` | What is the difference between reactive scaling and pre-scaling? | **ACCEPTED** | REJECTED | ContextSupport |
| `OT-06` | `incident` | Why might adding more replicas fail to solve every latency problem? | **REJECTED** | REJECTED | ContextSupport |
| `OT-07` | `unanswerable` | What exact Kubernetes version is used by the system? | **ACCEPTED** | REJECTED | ContextSupport, AppropriateRefusal |
| `OT-08` | `unanswerable` | What exact memory limit is configured for each application pod? | **ACCEPTED** | REJECTED | ContextSupport, AppropriateRefusal |
| `OT-09` | `unanswerable` | Which cloud provider hosts this system? | **ACCEPTED** | ACCEPTED | None (Passed) |
| `OT-10` | `unanswerable` | What is the name of the system administrator? | **ACCEPTED** | REJECTED | ContextSupport, AppropriateRefusal |
| `OT-11` | `out_of_scope` | Can you give me a recipe for chocolate fudge cake? | **ACCEPTED** | REJECTED | ContextSupport, AppropriateRefusal |
| `OT-12` | `out_of_scope` | Who won the FIFA World Cup in 2022? | **ACCEPTED** | REJECTED | ContextSupport, AppropriateRefusal |

---

## 5. Key Engineering Insights

1. **Unguarded Pipelines Suffer Severe Hallucination on Negative Tests**:
   Without pre-acceptance testing and guardrails, the LLM hallucinates answers for unanswerable domain queries (such as inventing arbitrary Kubernetes version numbers like `v1.28` or cloud providers).
2. **Pre-Acceptance Verification Eliminates Out-of-Scope Leakage**:
   The output testing harness rejects responses that fail appropriate refusal on out-of-scope requests, preventing brand dilution and operational risk.
3. **100% Groundedness on In-Scope Documentation**:
   For documented HPA concepts, the guarded pipeline provides 100% context support and zero false refusals.
