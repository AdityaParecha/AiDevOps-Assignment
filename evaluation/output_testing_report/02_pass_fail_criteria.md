# API Output Testing: Pass/Fail Criteria Explained in Plain English

This file explains what each check means and how the code decides whether an LLM output passes or fails.

## Source code
- evaluation/output_testing.py

## 1) Relevance
Question: Is the answer about the same topic as the user question?

How it is judged:
- the code checks whether the answer contains words related to the question
- if the answer is a refusal, it is treated as a valid refusal when the system is correctly saying the information is unavailable

Pass condition:
- the answer matches the question topic well enough
- the relevance score must be above the threshold

Fail condition:
- the answer is about a completely different topic
- for example, asking about Kubernetes autoscaling but getting a general answer about France or cooking

## 2) Context Support / Groundedness
Question: Is the answer supported by the retrieved context?

How it is judged:
- the answer is split into sentences
- the code checks whether the sentence vocabulary overlaps with the retrieved context
- if the answer is a refusal, it passes if the refusal is appropriate

Pass condition:
- most answer sentences are grounded in the provided context
- the score must be above the threshold

Fail condition:
- the answer invents details not present in the retrieved context
- the answer is disconnected from the source content

## 3) Unsupported Claims / Hallucination
Question: Does the answer contain claims that are not backed by the context?

How it is judged:
- the code looks for suspicious details such as exact version numbers, cloud providers, memory specs, and phone numbers
- it also checks whether the answer includes unsupported facts not found in the context

Pass condition:
- no unsupported or made-up claim is found

Fail condition:
- the answer says a version number, cloud provider, database, or memory limit that does not exist in the knowledge base
- the answer invents technical facts

## 4) Format Compliance
Question: Does the answer follow the expected format and safety rules?

How it is judged:
- the code checks whether the output contains blocked prompt-leak patterns
- it also checks for length or content problems
- it ensures the model does not reveal system instructions or internal prompts

Pass condition:
- the answer is properly formatted and does not leak system instructions
- it does not contain hidden prompt-injection patterns or unsafe content

Fail condition:
- the output reveals internal instructions
- the output is malformed, overly long, or suspiciously constructed

## 5) Sufficiency Answering
Question: Does the model answer the question when enough information is available?

How it is judged:
- if the user asks a valid question and the context contains enough information, the answer must provide a real answer

Pass condition:
- the output gives a useful, relevant answer instead of refusing unnecessarily

Fail condition:
- the model refuses even when the information is present
- or gives an evasive answer without actually addressing the question

## 6) Appropriate Refusal
Question: Does the model refuse only when it should?

How it is judged:
- the code checks for refusal language such as "The provided knowledge base does not contain enough information"
- it compares refusal behavior against missing or out-of-scope questions

Pass condition:
- the model refuses when facts are missing or the question is outside domain

Fail condition:
- the model answers a question that should have been refused
- or it refuses a question that should have been answered with the available context

## Overall verdict
The system combines all six checks and decides:
- ACCEPTED if the output passes the needed conditions
- REJECTED if it fails one or more required checks

This is a pre-acceptance gate: the application should not send the output to the user if it fails the quality and safety checks.
