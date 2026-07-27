# Qwen3.6 Safe-Boundary Partial Tool-Window Validation

## Document purpose

This document continues after:

    QWEN36_SLOT_AFFINITY_FLAG_TEMPLATE_FINAL_VALIDATED.md

That previous document validated:

    Slot affinity flag and repo-scope slot isolation
    Final Aibsu enhanced empty-think items template
    Local Edit argument canonicalization
    General schema canonicalization kept OFF
    NP2 OpenClaude A/B coding baseline

This document validates the later safe-boundary checkpoint and partial reprefill line.

---

## Final validated engine line

Active development branch:

    qwen36-safe-boundary-only-partial-reprefill-v1

Final stable branch pointer:

    qwen36-stable-safe-boundary-partial-tool-window

Final tag:

    qwen36-safe-boundary-partial-tool-window-v1

Final commit:

    44770bfbf Allow safe-boundary partial reprefill on tool mismatch

Previous relevant commits in this line:

    2c1f701c8 Diagnose mixed ubatch scope contamination
    94d70f67d Add safe boundary only periodic checkpoints
    f2dd18758 Document Qwen3.6 slot affinity flag and final template validation
    86a33032d Add optional repo-scope slot affinity flag
    19720584b Document Qwen3.6 Edit argument roundtrip validation
    40aa1c99f Canonicalize Edit tool arguments for Qwen3.6 roundtrip
    0770f3f95 Document NP2 slot affinity tool edit guard validation

Final interpretation:

    This line extends the validated NP2 slot-affinity/template/Edit-canonicalization baseline with safe-boundary-only checkpoints and safe-boundary partial reprefill.

---

## Runtime preset validated for this line

Model:

    ~/models/gguf/Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf

Validated command:

    ./llama-server \
      -m ~/models/gguf/Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf \
      --host 0.0.0.0 \
      --port 8080 \
      -sm graph \
      --max-gpu 2 \
      -ts 57,43 \
      -ngl 999 \
      --flash-attn on \
      -ctk q8_0 \
      -ctv q8_0 \
      -c 122880 \
      -np 2 \
      -b 2048 \
      -ub 1024 \
      --ctx-checkpoints 16 \
      --ctx-checkpoints-interval 4096 \
      --ctx-checkpoints-safe-boundary-only \
      --slot-prompt-similarity 0.3 \
      --slot-affinity-by-repo-scope \
      --threads 16 \
      --threads-batch 24 \
      --temp 0.6 \
      --top-p 0.95 \
      --top-k 20 \
      --min-p 0.0 \
      --presence-penalty 0.0 \
      --repeat-penalty 1.05 \
      --scheduler_async \
      --reasoning off \
      --reasoning-tokens none \
      --jinja \
      --chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja \
      --chat-template-kwargs '{"preserve_thinking":true}'

Runtime interpretation:

    Total context: 122880
    Parallel slots: 2
    Effective context per slot: 61440
    GPU split: 57,43
    Batch: 2048
    Ubatch: 1024
    Checkpoints: 16
    Checkpoint interval: 4096
    Safe-boundary-only checkpoints: enabled
    Slot prompt similarity: 0.3
    Repo-scope slot affinity: enabled
    Prompt cache: enabled
    Reasoning: disabled
    Template: final Aibsu enhanced empty-think items template

---

## Validated hardware

Validated on:

    2x NVIDIA GeForce RTX 4080 SUPER
    Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf
    ik_llama.cpp
    OpenClaude local agents

Observed model initialization:

    n_ctx = 122880
    n_slots = 2
    n_ctx_slot = 61440
    KV self size around 4080 MiB with q8_0 K/V
    Prompt cache enabled

---

## Main validated change 1: safe-boundary-only periodic checkpoints

Commit:

    94d70f67d Add safe boundary only periodic checkpoints

New CLI flag:

    --ctx-checkpoints-safe-boundary-only

Purpose:

    Prevent arbitrary base checkpoints inside unsafe prompt/tool regions.
    Create recurrent checkpoints only at safe message boundaries derived from message_spans.
    Use ctx_checkpoints_interval as the cadence for pending periodic safe-boundary checkpoints.

Expected checkpoint source:

    message_spans_periodic

Expected checkpoint types:

    user_start
    user_end
    user_boundary

Expected skip logs:

    QWEN36_SAFE_BOUNDARY_ONLY_SKIP_BASE_CHECKPOINT_V1: reason=prompt_end
    QWEN36_SAFE_BOUNDARY_ONLY_SKIP_BASE_CHECKPOINT_V1: reason=final_response

Meaning:

    Base checkpoints at prompt end or final response are skipped when safe-boundary-only is active.
    Checkpoints should come from safe message boundaries instead.

---

## Main validated change 2: initial anchor-on-crossing checkpoint

Problem found:

    The first attempt created a late checkpoint labeled as user_start.
    Example of the wrong behavior:

        selected_boundary=4118
        pos=10021
        checkpoint n_tokens=10022

    That meant metadata said user_start, but the physical checkpoint was actually late.

Corrected behavior:

    Create the first checkpoint physically when prompt processing crosses n_before_user/user_start.
    Cut the current batch at that crossing.
    Create the checkpoint immediately at the real user_start token position.

Expected log:

    QWEN36_SAFE_BOUNDARY_ONLY_ANCHOR_ON_CROSSING_V1

Validated examples:

    Agent A:

        n_past_prompt=4120
        n_past=4120
        initial_anchor=1
        checkpoint n_tokens=4120
        type=user_start
        source=message_spans_periodic

    Agent B:

        n_past_prompt=4118
        n_past=4118
        initial_anchor=1
        checkpoint n_tokens=4118
        type=user_start
        source=message_spans_periodic

Final interpretation:

    The first safe checkpoint is now a real early anchor at the first user_start/n_before_user.
    It is not just metadata attached to a later KV state.

---

## Main validated change 3: periodic checkpoint after anchor

After the initial anchor, periodic safe-boundary checkpoints are counted from the last real checkpoint.

Validated pattern:

    First checkpoint:

        user_start around 4118 or 4120

    Second checkpoint:

        user_end around 10013, 10014, 12595, or 12596 depending on prompt size

Example pattern:

    previous_checkpoint=4118
    selected_boundary=12596
    type=user_end
    source=message_spans_periodic
    checkpoint n_tokens=12604

Interpretation:

    The first anchor starts the cadence.
    The next periodic safe checkpoint is created at a later safe user boundary after interval eligibility.

---

## Main validated change 4: safe-boundary partial reprefill window

Policy:

    When a recurrent cache/prompt mismatch occurs, partial reprefill is allowed only if a safe checkpoint exists far enough behind the mismatch.

Core rule:

    selected_checkpoint <= exact_prefix - ctx_checkpoints_interval

With the validated interval:

    ctx_checkpoints_interval = 4096

Example validated case:

    exact_prefix=13996
    min_window=4096
    max_checkpoint=9900
    selected_checkpoint=4118
    actual_window=9878
    prompt_tokens=14051
    tokens_to_prefill=9933

Interpretation:

    The mismatch happened near 13996.
    The selected checkpoint was at 4118.
    The distance from checkpoint to mismatch was 9878 tokens.
    That is safely above the 4096-token minimum window.
    Partial reprefill was allowed.

---

## Main validated change 5: tool mismatch window policy

Previous misleading log:

    COMMON_PREFIX_MISMATCH_SKIP_PARTIAL_TOOL_EDIT_V1
    action=full_clean_prefill

Why it was misleading:

    The code was no longer strictly using the old policy "tool mismatch always means full clean prefill."
    The new policy allows partial reprefill even with tool mismatch if the safe-boundary window is valid.

New policy log:

    COMMON_PREFIX_MISMATCH_TOOL_EDIT_WINDOW_POLICY_V1

Expected meaning:

    Tool/edit mismatch was detected.
    The server will evaluate whether a safe-boundary checkpoint exists far enough behind the mismatch.
    It does not automatically force full prefill.

Expected successful partial log:

    COMMON_PREFIX_MISMATCH_RECURRENT_PARTIAL_REPREFILL_MIN_V1
    mode=safe_boundary_window
    tool_edit_mismatch=1
    action=allow_partial
    reason=safe_boundary_window_ok

Expected fallback log:

    QWEN36_SAFE_BOUNDARY_ONLY_PARTIAL_FALLBACK_FULL_PREFILL_V1
    tool_edit_mismatch=1
    action=full_clean_prefill
    reason=no_safe_boundary_window_candidate

Final policy:

    tool_edit_mismatch + safe_boundary_window_ok:
        allow partial reprefill

    tool_edit_mismatch + no valid safe checkpoint:
        full clean prefill

---

## Main validated change 6: mixed ubatch diagnostic

Commit:

    2c1f701c8 Diagnose mixed ubatch scope contamination

Marker:

    QWEN36_MIXED_UBATCH_DIAG_V1

Observed pattern:

    selected=2
    same_seq=1
    unique_prefix=2
    pattern_first16=[0,1,...]
    pattern_first16=[1,0,...]

Interpretation:

    The recurrent-safe ubatch sizing can still select a mixed two-sequence prefix under the current max_same_or_unique_prefix policy.
    This was observed multiple times during A/B tests.
    It did not cause visible A/B path contamination in the successful runs.

Status:

    Diagnostic retained in this line.
    Not yet promoted as a same-seq-only policy change.
    Future work may compare current policy against same-seq-only.

---

## Validated A/B test behavior

Agent A repo:

    ~/ai-stack/agents/openclaude/test-repos/oc-agent-a-benchmark

Agent B repo:

    ~/ai-stack/agents/openclaude/test-repos/oc-agent-b-benchmark

Agent A task:

    Keep add(a, b)
    Add math utilities:
        subtract
        multiply
        divide
        square
        cube
        is_even
        is_odd
        factorial
        clamp
        average

Agent B task:

    Keep add(a, b)
    Add string utilities:
        reverse_text
        uppercase_text
        lowercase_text
        count_words
        is_palindrome
        remove_spaces
        count_vowels
        starts_with
        ends_with
        title_case

Validation used:

    python3 -m pytest -q
    AST function-name validation
    git diff review

Observed results:

    Agent A:
        23 passed
        FUNCTION_NAME_CHECK_PASSED

    Agent B:
        21 passed
        FUNCTION_NAME_CHECK_PASSED

Important interpretation:

    Agent A often adds extra tests around factorial, clamp, or average.
    That is prompt compliance drift, not engine/cache contamination.
    Function identifiers remained correct.
    Agent B matched the expected 21 tests exactly.

---

## Slot affinity validation retained

Expected slot routing:

    Agent A -> key=a -> slot=0
    Agent B -> key=b -> slot=1

Expected marker:

    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V2

Validated behavior:

    A continued using oc-agent-a-benchmark paths.
    B continued using oc-agent-b-benchmark paths.
    Busy matching slots deferred instead of crossing into another repo slot.
    No visible A/B route contamination was observed in the successful validation runs.

Interpretation:

    Slot affinity V2 remains compatible with safe-boundary partial reprefill.

---

## Edit canonicalization validation retained

Expected markers:

    QWEN36_TOOL_ARG_ROUNDTRIP_FROM_OAI_V1
    QWEN36_TOOL_ARG_ROUNDTRIP_TO_JSON_V1

Observed behavior:

    Read, Edit, and Bash tool arguments roundtripped correctly.
    Local Edit canonicalization kept file_path, old_string, new_string ordering.
    replace_all:false was canonicalized away where expected.

Interpretation:

    The safe-boundary partial line does not remove the prior local Edit canonicalization behavior.

---

## Healthy expected logs

### Initial anchor

Expected:

    QWEN36_SAFE_BOUNDARY_ONLY_ANCHOR_ON_CROSSING_V1
    initial_anchor=1
    checkpoint_count=0

Expected physical checkpoint:

    checkpoint metadata:
    n_tokens=4118 or 4120
    type=user_start
    source=message_spans_periodic

### Periodic checkpoint

Expected:

    QWEN36_SAFE_BOUNDARY_ONLY_BOUNDARY_DECISION_V1
    action=create
    source=message_spans_periodic

Expected physical checkpoint:

    type=user_end
    source=message_spans_periodic

### Tool mismatch safe-window partial

Expected:

    COMMON_PREFIX_MISMATCH_TOOL_EDIT_WINDOW_POLICY_V1
    action=evaluate_safe_boundary_window
    reason=tool_edit_mismatch

Then, if window is valid:

    COMMON_PREFIX_MISMATCH_RECURRENT_PARTIAL_REPREFILL_MIN_V1
    mode=safe_boundary_window
    tool_edit_mismatch=1
    action=allow_partial
    reason=safe_boundary_window_ok

Then:

    restored context checkpoint

### Tool mismatch fallback

Expected if no safe candidate exists:

    QWEN36_SAFE_BOUNDARY_ONLY_PARTIAL_FALLBACK_FULL_PREFILL_V1
    tool_edit_mismatch=1
    action=full_clean_prefill
    reason=no_safe_boundary_window_candidate

Then:

    COMMON_PREFIX_MISMATCH_RECURRENT_REPREFILL

### Mixed ubatch diagnostic

Expected while diagnostic is retained:

    QWEN36_MIXED_UBATCH_DIAG_V1
    policy=max_same_or_unique_prefix

Interpretation:

    This is diagnostic noise, not necessarily failure.
    Investigate only if it correlates with A/B contamination or tool-path drift.

---

## Performance observations

Large prompt eval examples:

    Around 8.5K tokens:
        1437-1548 tok/s prompt eval

    Around 12.6K tokens:
        1437-1648 tok/s prompt eval

Small incremental prompt eval:

    Can appear much lower due overhead and concurrent generation.

Generation observations:

    Tool-heavy concurrent generation often around 10-16 tok/s.
    Some long turns may dominate total elapsed time.

Partial reprefill observed:

    selected_checkpoint=4118
    prompt_tokens=14051
    tokens_to_prefill=9933
    took around 44 ms for checkpoint restore path in the observed run

Interpretation:

    Partial reprefill reduces unsafe cache reuse while avoiding a full restart from token 0 when a safe checkpoint exists sufficiently far behind the mismatch.

---

## Important nuance: full prefill still happens

Full prefill is still expected when:

    exact_prefix is very small
    max_checkpoint is negative
    no safe-boundary checkpoint exists
    safe checkpoint exists but is too close to the mismatch
    checkpoint restore fails

Example:

    exact_prefix=3
    min_window=4096
    max_checkpoint=-4093

Interpretation:

    Partial cannot be used there.
    Clean prefill is correct.

Cold restart interpretation:

    After cold mismatch, the corrected anchor-on-crossing logic rebuilds a real early checkpoint during the new clean prefill.

---

## Current stable experimental recommendation

Use this line as the current validated experimental baseline for Qwen3.6 NP2 multiagent OpenClaude testing:

    Engine branch:
        qwen36-stable-safe-boundary-partial-tool-window

    Engine tag:
        qwen36-safe-boundary-partial-tool-window-v1

    Template branch:
        qwen36-stable-aibsu-enhanced-empty-think-items

    Runtime additions:
        --ctx-checkpoints-safe-boundary-only
        --slot-affinity-by-repo-scope
        --chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja
        --chat-template-kwargs '{"preserve_thinking":true}'

Keep enabled:

    Prompt cache
    Local Edit canonicalization
    Repo-scope slot affinity
    Safe-boundary-only checkpoints
    Safe-boundary partial reprefill window

Keep OFF:

    Global schema canonicalization for all tools unless testing an experimental branch
    cache-ram 0 unless debugging prompt cache
    Same-seq-only ubatch policy unless testing a separate causal branch

---

## Recommended next tests

### 1. Repeat A/B 48K equivalent with true token expansion

The previous 48K-character prompt produced around 14K prompt tokens, not 48K tokens.

If true 48K token stress is needed, increase the diagnostic text substantially or generate token-heavy structured text.

Goal:

    More safe checkpoints
    Higher exact_prefix mismatches
    More opportunities to select mid checkpoints around 8K, 12K, 16K, etc.

### 2. Test same-seq-only ubatch as a separate experiment

Current diagnostic shows mixed sequence batches:

    selected=2
    same_seq=1
    unique_prefix=2

Experiment:

    selected = n_tokens_same_seq

Goal:

    Determine whether mixed initial ubatches contribute to rare A/B contamination or tool-flow instability.

Do not merge same-seq-only into this stable experimental line without separate validation.

### 3. Preserve strict AST validation prompts

Keep requiring:

    pytest
    AST function-name validation
    git diff

Reason:

    Pytest alone can pass even when the agent violates the requested public API.

---

## Final conclusion

The current line validates a safer and more useful recurrent checkpoint strategy for Qwen3.6 NP2 OpenClaude multiagent workflows.

Main achievement:

    The first checkpoint is now created physically at the first safe user_start/n_before_user boundary.
    Periodic checkpoints then continue from that real anchor.
    Partial reprefill can use a safe-boundary checkpoint even during tool mismatch, as long as the selected checkpoint is at least ctx_interval behind exact_prefix.

Validated policy:

    safe checkpoint far enough behind mismatch:
        partial reprefill allowed

    no safe checkpoint or checkpoint too close:
        full clean prefill

Main result:

    The system successfully used selected_checkpoint=4118 for exact_prefix=13996 with actual_window=9878 and tokens_to_prefill=9933.
    This validates the safe_boundary_window policy in a real OpenClaude tool-heavy run.

Main caution:

    The line still contains mixed ubatch diagnostics and should be treated as stable experimental, not upstream-clean production.
    Same-seq-only ubatch remains a separate future experiment.
