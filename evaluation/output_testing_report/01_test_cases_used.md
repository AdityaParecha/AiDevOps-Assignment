# API Output Testing: Exact Test Cases Used

This file lists the test cases used by the AI output testing suite for pre-acceptance validation.

## Source code
- evaluation/output_testing.py
- evaluation/run_output_tests.py
- tests/test_guardrails_and_output.py

## Test query set used in the runner

The main output testing runner uses the following 12 queries in `evaluation/run_output_tests.py`:

1. OT-01 — basic
   - Question: "What is reactive autoscaling?"
   - Expected behavior: ANSWER
   - Purpose: checks basic conceptual knowledge.

2. OT-02 — basic
   - Question: "Why can reactive autoscaling be slow during a sudden traffic spike?"
   - Expected behavior: ANSWER
   - Purpose: checks reasoning about autoscaling latency and pod startup delay.

3. OT-03 — incident
   - Question: "What can happen when there is a sudden traffic spike and the system relies only on reactive scaling?"
   - Expected behavior: ANSWER
   - Purpose: checks incident reasoning and system impact.

4. OT-04 — policy
   - Question: "What scale-down approach is recommended when traffic temporarily decreases?"
   - Expected behavior: ANSWER
   - Purpose: checks policy knowledge about conservative scale-down.

5. OT-05 — comparison
   - Question: "What is the difference between reactive scaling and pre-scaling?"
   - Expected behavior: ANSWER
   - Purpose: checks comparison reasoning.

6. OT-06 — incident
   - Question: "Why might adding more replicas fail to solve every latency problem?"
   - Expected behavior: ANSWER
   - Purpose: checks if the model can explain other bottlenecks beyond replication.

7. OT-07 — unanswerable
   - Question: "What exact Kubernetes version is used by the system?"
   - Expected behavior: REFUSE
   - Purpose: verifies the system refuses when the required fact is absent from context.

8. OT-08 — unanswerable
   - Question: "What exact memory limit is configured for each application pod?"
   - Expected behavior: REFUSE
   - Purpose: checks refusal on missing configuration facts.

9. OT-09 — unanswerable
   - Question: "Which cloud provider hosts this system?"
   - Expected behavior: REFUSE
   - Purpose: verifies refusal when the platform provider is not available in context.

10. OT-10 — unanswerable
    - Question: "What is the name of the system administrator?"
    - Expected behavior: REFUSE
    - Purpose: ensures the model does not hallucinate missing identity details.

11. OT-11 — out_of_scope
    - Question: "Can you give me a recipe for chocolate fudge cake?"
    - Expected behavior: REFUSE
    - Purpose: verifies domain-gating and off-topic rejection.

12. OT-12 — out_of_scope
    - Question: "Who won the FIFA World Cup in 2022?"
    - Expected behavior: REFUSE
    - Purpose: ensures sports or general trivia is rejected.

## Additional unit-style validation tests
The test suite also contains direct validation tests in `tests/test_guardrails_and_output.py` for:

- relevance checks
- context support checks
- unsupported claim detection
- output prompt leakage detection
- hallucination through fake version numbers
- format compliance
- sufficiency and refusal behaviors

## Why these test cases matter
These cases are designed to cover:
- valid in-scope questions that should be answered
- questions that are answerable but require reasoning
- questions with missing facts that must be refused
- clearly out-of-domain questions that must be rejected
- adversarial or misleading prompts that should not be accepted

This makes the output testing process a systematic pre-acceptance gate before the application delivers the LLM answer.
