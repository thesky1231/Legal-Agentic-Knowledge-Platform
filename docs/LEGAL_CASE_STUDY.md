# Legal Case Study

## Positioning

This repository now absorbs the strongest parts of the earlier `Legal-AI` project into the current agent platform story.

Instead of presenting:

- one generic agent backend demo
- one separate legal RAG demo

the project can now be described as:

`a legal-domain agentic knowledge platform with evaluation, refusal control, and production-oriented backend engineering`

## What Was Carried Over

- Legal answer evaluation dataset: `examples/legal/answer_eval_dataset.json`
- Legal retrieval golden set: `examples/legal/retrieval_eval_dataset.json`
- Historical answer-level metrics snapshot from the original project
- Historical retrieval-level metrics snapshot from the original project
- Question classification and conservative refusal strategy inspired by the legal use case

## Historical Metrics From The Original Legal Project

The imported reference metrics capture the strongest evidence from the previous legal RAG system:

- Answer evaluation dataset size: `15`
- Answer correct rate: `100%`
- Citation correct rate: `100%`
- Hallucination rate: `0%`
- Refusal appropriate rate: `100%`
- Avg overall score: `3.0`

Retrieval evaluation on the second golden dataset:

- Dataset size: `20`
- Vector Recall@3: `95%`
- Vector Recall@5: `95%`
- Hybrid Recall@3: `95%`
- Hybrid Recall@5: `95%`

These values come from the imported reference files under `examples/legal/`.

## What Is Now Reflected In The Current Platform

- The knowledge base now classifies incoming questions into `direct_answer`, `definition`, `confusing`, `complex_reasoning`, and `should_refuse`.
- The answer layer can trigger conservative refusal or low-confidence fallback behavior instead of forcing an unsafe direct answer.
- The evaluation loader now accepts both the platform-native dataset schema and the older legal project list-style schema.
- Agent responses now expose `question_type`, `confidence`, and `refusal_triggered`, which makes policy behavior visible in API responses, demos, and audit logs.

## How To Tell The Story In Interviews

Use this project as a single main case:

1. Start from the legal use case: legal QA requires citation grounding, refusal control, and lower hallucination risk.
2. Explain how retrieval and answer evaluation datasets were built to measure both recall and answer behavior.
3. Show that the final backend is not a narrow legal script, but a reusable agent platform with observability, auth, audit, and multi-agent execution.
4. Emphasize that the legal scenario proved the platform under a higher-risk domain than generic enterprise handbook QA.
