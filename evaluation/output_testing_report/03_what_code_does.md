# What Code Is Used for What

This file explains which code handles which part of the testing workflow.

## 1) Output testing logic
File:
- evaluation/output_testing.py

Purpose:
- defines the AI output validation engine
- implements the pass/fail checks for relevance, context support, hallucination, format compliance, sufficiency, and refusal
- contains the `AIOutputTester` class and each test method

## 2) Runner that executes the test cases
File:
- evaluation/run_output_tests.py

Purpose:
- defines the actual `TEST_QUERIES` list
- runs each question once with guardrails enabled and once with guardrails disabled
- calls `AIOutputTester.evaluate_output()`
- compares guarded vs unguarded output acceptance
- saves the JSON and Markdown reports

## 3) Unit/integration tests for guardrails and output validation
File:
- tests/test_guardrails_and_output.py

Purpose:
- validates the lower-level guardrail behavior
- validates the output-testing logic itself with direct assertions
- ensures certain prompts are blocked and certain valid prompts are allowed
- checks hallucination and unsupported claim detection in unit-style tests

## 4) Result files generated
Files:
- evaluation/output_test_results.json
- evaluation/output_test_report.md

Purpose:
- store the detailed evaluation outcomes
- summarize acceptance rates and condition-wise pass rates

## 5) Guardrail-related code used in the pipeline
File:
- services/pipeline.py

Purpose:
- executes the application pipeline
- toggles guardrails on or off
- provides answers used by the testing suite

## 6) Underlying guardrail implementation
File:
- services/guardrails.py

Purpose:
- implements input, retrieval, and output guardrails
- blocks malicious / off-topic queries and sanitizes unsafe outputs

## Summary of workflow

The overall flow is:

1. User asks a query
2. The pipeline processes the query
3. With guardrails enabled, unsafe or off-scope input is blocked
4. The generated candidate answer is evaluated using `AIOutputTester`
5. If it fails any required condition, it is rejected before being accepted
6. Results are saved into JSON and Markdown reports

This is the systematic API output testing process used in the project.
