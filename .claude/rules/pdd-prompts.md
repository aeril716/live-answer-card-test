# PDD prompts

Before writing or editing any file under `prompts/`, read
[docs/writing-pdd-prompts.md](../../docs/writing-pdd-prompts.md).

The GitHub issues are NOT prompts — they contain scheduling, demo risk, and
prize strategy that must not reach the model.
[prompts/retrieval_python.prompt](../../prompts/retrieval_python.prompt) is the
reference conversion of the Lane 1 retrieval issue
(`ignore-gameplan.context/lane1_mock_issue.md`).

Shared product constraints and the five frozen interfaces live in
[context/project_preamble.prompt](../../context/project_preamble.prompt) —
every module prompt includes it and never restates it.
