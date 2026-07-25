## Step 12: Fix Issues (Iteration 5/5)

**Status:** Fixes Applied

### Fixes Made

1. **Fixed** `docs/writing-pdd-prompts.md` lines 37-40 and 88-94
   - Issue: The Lane 3 trigger/model-client guidance incorrectly cited issue #3 and described nonexistent mutual header-comment cross-references.
   - Fix: Changed the references to issue #10 and documented the current one-way `<pdd-dependency>` from the trigger prompt to the model-client prompt.

2. **Fixed** `docs/writing-pdd-prompts.md` lines 41-47
   - Issue: The guide said every prompt starts with the shared preamble include, conflicting with the leading `<pdd-*>` architecture metadata used by both Lane 3 prompts.
   - Fix: Clarified that the shared preamble include follows any leading architecture metadata and that fallback inlining belongs in the same position.

### Summary
Applied 2 fixes successfully. Verified the shared preamble include target exists, the prompt metadata/dependency ordering matches the guide, no stale issue #3 or mutual-cross-reference wording remains, and `git diff --check` passes.

---
*Returning to Step 11 for re-verification*
