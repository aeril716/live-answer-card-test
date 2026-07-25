## Step 12: Fix Issues (Iteration 3/5)

**Status:** Fixes Applied

### Fixes Made

1. **Fixed** `prompts/audio_python.prompt` line 51
   - Issue: Failure containment applied only to an “ordinary” internal failure, weakening the frozen no-raise contract.
   - Fix: Required a fresh EMPTY dictionary for any internal failure without raising under any circumstance, while retaining the explicit stdout-failure behavior.

2. **Fixed** `prompts/_TEMPLATE_module_python.prompt` line 5
   - Issue: The advertised repository template used legacy headings that conflicted with the guide’s required four-section prompt structure.
   - Fix: Replaced the legacy scaffold with metadata-aware `% Goal`, `% Role & Scope`, `% Requirements`, and `% Deliverables` sections while preserving frozen-interface, behavioral-contract, no-raise, import-restriction, logging, validation, and done-condition guidance.

### Summary
Applied 2 fixes successfully.

---
*Returning to Step 11 for re-verification*
