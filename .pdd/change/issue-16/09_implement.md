## Step 9: Implement Changes

**Status:** Changes Applied

### Files Modified
FILES_MODIFIED: README.md, docs/writing-pdd-prompts.md

### Files Created
FILES_CREATED: prompts/audio_python.prompt

### Direct Edits
None.

### Summary of Changes

#### `prompts/audio_python.prompt` (new)
- Created the prompt-native contract for the non-blocking, network-free audio mock.
- Added nine requirements covering the frozen return shape, ordered exactly-once replay, increasing timestamps, permanent exhaustion, defensive copies, failure containment, per-call logging, and six-call validation.

#### `README.md`
- Added the approved Audio mock section with sequence, exhaustion, logging, and offline validation guidance.

#### `docs/writing-pdd-prompts.md`
- Added `audio_python.prompt` to the repository prompt inventory.

### Scope Validation
- Only prompt and documentation files were changed.
- No generated code, examples, tests, or direct-edit candidates were modified.
- Duplication review confirmed that no existing module owns utterance acquisition or replay state.

SCOPE_VIOLATION: No

### Worktree Location
Changes are in: `/tmp/pdd_job_pwlYgJtJT7l3U1OEcun5_pg_oucfu/.pdd/worktrees/change-issue-16`

### Next Steps
After review, run `pdd sync` on the new prompt to generate code, example, and tests.

---
*Proceeding to Step 10: Identify Issues*
