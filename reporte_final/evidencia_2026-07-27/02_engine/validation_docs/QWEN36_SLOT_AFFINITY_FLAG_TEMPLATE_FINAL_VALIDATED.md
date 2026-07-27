# Qwen3.6 Slot Affinity Flag + Final Template Validation

## Final validated engine line

Branch used during development:

    qwen36-investigate-cache-prompt-tool-edit-mismatch

Final stable branch pointer:

    qwen36-stable-slot-affinity-flag-default-off

Final tag:

    qwen36-slot-affinity-flag-default-off

Final commit:

    86a33032d Add optional repo-scope slot affinity flag

Previous relevant commits:

    19720584b Document Qwen3.6 Edit argument roundtrip validation
    40aa1c99f Canonicalize Edit tool arguments for Qwen3.6 roundtrip
    0770f3f95 Document NP2 slot affinity tool edit guard validation
    bae6c70cf Guard partial reprefill on tool edit mismatches

Final interpretation:

    Slot affinity by repo scope is now configurable.
    Default is OFF.
    It is enabled explicitly with --slot-affinity-by-repo-scope.

---

## Final validated template line

Template repo:

    ~/ai-stack/templates

Template stable branch pointer:

    qwen36-stable-aibsu-enhanced-empty-think-items

Template tag:

    qwen36-aibsu-enhanced-empty-think-items-v1

Template commit:

    98d611f Add final Qwen3.6 Aibsu enhanced template

Template cleanup commit:

    e8c0843 Ignore non-final template artifacts

Final active template files:

    ~/ai-stack/templates/qwen3.6/chat_template.jinja
    ~/ai-stack/templates/qwen3.6/chat_template.qwen36-aibsu-enhanced-empty-think-items-v1.jinja

SHA256:

    3a4edb004f4e3b67077b5bb084688f2ef8846495ccba51de160d87102681110f  chat_template.jinja
    3a4edb004f4e3b67077b5bb084688f2ef8846495ccba51de160d87102681110f  chat_template.qwen36-aibsu-enhanced-empty-think-items-v1.jinja

Required active template markers:

    QWEN36_STABLE_EMPTY_THINK_FRAME_V1
    QWEN36_AIBSU_TOOL_ARGUMENT_ITEMS_V1

Important template behavior:

    Assistant history keeps empty <think></think> frame symmetry when thinking is disabled.
    Tool arguments are rendered with tool_call.arguments|items.
    The template preserves backend/canonical argument order instead of forcing dictsort.

Rejected older template behaviors:

    QWEN36_NO_EMPTY_THINK_FRAME_V2
    QWEN36_CANONICAL_TOOL_ARG_ORDER_V1 as global dictsort in template

Final interpretation:

    Use the Aibsu enhanced template as the base.
    Keep empty-think symmetry.
    Do not sort tool arguments globally in the template.
    Let the backend/local Edit canonicalizer control Edit argument order.

---

## Final validated runtime preset

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
    Slot prompt similarity: 0.3
    Repo-scope slot affinity: enabled explicitly
    Prompt cache: enabled
    Reasoning: disabled
    Reasoning tokens: none
    Template: final Aibsu enhanced empty-think items template

---

## Validated hardware

Validated on:

    2x NVIDIA GeForce RTX 4080 SUPER
    Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf
    ik_llama.cpp
    OpenClaude local agents

Expected VRAM behavior:

    GPU0/GPU1 typically around 14-15 GiB used depending on slot load, display load, checkpoint state, and active generation.

---

## What changed in this final line

### 1. Slot affinity flag

Previous behavior:

    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1 = true
    SLOT_AFFINITY_BY_REPO_SCOPE_V1 = true

Final behavior:

    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1 = slot_affinity_by_repo_scope
    SLOT_AFFINITY_BY_REPO_SCOPE_V1 = slot_affinity_by_repo_scope

New CLI flag:

    --slot-affinity-by-repo-scope

Default:

    false

Meaning:

    By default, upstream-like slot behavior is preserved.
    Repo-scope slot affinity is only activated when explicitly requested.

Files changed:

    common/common.h
    common/common.cpp
    examples/server/server-context.h
    examples/server/server-context.cpp
    examples/server/server.cpp

---

### 2. Local Edit argument canonicalization retained

Local Edit canonicalizer remains active in:

    common/chat.cpp

Expected markers:

    qwen36_canonicalize_edit_arguments_v1
    QWEN36_TOOL_ARG_ROUNDTRIP_FROM_OAI_V1
    QWEN36_TOOL_ARG_ROUNDTRIP_TO_JSON_V1

Purpose:

    Canonicalize only Edit tool arguments during OpenAI-compatible roundtrip.
    Keep order:
    file_path -> old_string -> new_string -> replace_all only when meaningful.
    Remove replace_all:false from reconstructed Edit payload.

Important interpretation:

    replace_all:false enters from OpenClaude/history payload.
    The local Edit canonicalizer removes it before the Edit payload is rendered back into model-visible history.

---

### 3. General schema canonicalization rejected for stable

Tested general schema canonicalization marker:

    QWEN36_SCHEMA_TOOL_ARGS_CANONICAL_V1

Final stable status:

    OFF

Expected binary verification:

    strings build/bin/llama-server | grep "QWEN36_SCHEMA_TOOL_ARGS_CANONICAL_V1" || echo "OK: general schema canonicalizer OFF"

Expected source verification:

    grep -n "QWEN36_SCHEMA_TOOL_ARGS_CANONICAL_V1\|qwen36_canonicalize_message_tool_arguments_by_schema_v1\|qwen36_build_tool_argument_orders_v1" examples/server/server-common.cpp || echo "OK: server-common.cpp general OFF"

Reason:

    General schema canonicalization can work, but it is not necessary for the original Edit old_string/new_string/replace_all mismatch.
    It touches more surface area than required because it can reorder all tools by schema.
    The stable line keeps the smaller, safer intervention: local Edit canonicalization only.

Important nuance:

    Testing did not conclusively prove general schema canonicalization is broken.
    With strict prompts, both General ON and General OFF completed A/B once.
    The stable decision is based on minimal intervention and lower surface area, not absolute failure of General ON.

---

## Validation history

### A/B strict prompt with General OFF + local Edit ON

Configuration:

    -np 2
    --slot-affinity-by-repo-scope
    General schema canonicalization OFF
    Local Edit canonicalization ON
    Final Aibsu enhanced template
    Strict function-name validation prompts

Result:

    Agent A: math utilities completed
    Agent B: string utilities completed
    Function-name validation passed for both
    No visible cross-agent contamination
    No cache scope mismatch observed
    No GGML_ASSERT

Observed result:

    Agent A: FUNCTION_NAME_CHECK_PASSED
    Agent B: FUNCTION_NAME_CHECK_PASSED

Notes:

    Agent A sometimes exceeded exact test-count instruction by adding one extra test.
    This is prompt compliance drift, not engine/cache corruption.

---

### A/B strict prompt with General ON + local Edit ON

Configuration:

    -np 2
    --slot-affinity-by-repo-scope
    General schema canonicalization ON
    Local Edit canonicalization ON
    Final Aibsu enhanced template
    Strict function-name validation prompts

Result:

    Agent A: math utilities completed in the final retry
    Agent B: string utilities completed
    Function-name validation passed for both

Important observation:

    One prior General ON run showed Agent A exiting early without modifying files.
    A later General ON run completed correctly.
    Therefore General ON is not conclusively invalid, but it remains unnecessary for stable.

Final interpretation:

    The strict prompt improved correctness strongly.
    General schema canonicalization was not required to pass.

---

## Strict validation prompt lesson

The earlier less strict prompts allowed semantic drift:

    Wrong names such as reverse instead of reverse_text
    Wrong names such as capitalize instead of uppercase_text
    Extra/missing functions
    Agent finishing with tests that passed only because tests matched the wrong implementation

The strict prompts fixed this by requiring:

    Exact public function identifiers
    AST-based function-name validation
    pytest validation
    git diff review

Recommended future agent prompt requirement:

    Always include explicit function-name validation when testing model/tool correctness.
    Do not rely only on pytest if the agent writes its own tests.

Reason:

    A model can pass self-written tests while violating the requested public API.
    AST identifier checks catch this.

---

## Healthy expected logs

### Slot affinity

Expected when flag is enabled:

    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=a slot=0 action=select reason=init
    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=a slot=0 action=select reason=match
    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=b slot=1 action=select reason=init
    SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=b slot=1 action=select reason=match

Expected interpretation:

    Agent A keeps returning to key=a slot.
    Agent B keeps returning to key=b slot.
    If a matching slot is busy, request should defer instead of crossing into the other repo slot.

### Edit canonical roundtrip

Expected:

    QWEN36_TOOL_ARG_ROUNDTRIP_FROM_OAI_V1
    QWEN36_TOOL_ARG_ROUNDTRIP_TO_JSON_V1

Healthy Edit pattern:

    raw_arguments:
    {"replace_all":false,"file_path":...,"old_string":...,"new_string":...}

    canonical_arguments:
    {"file_path":...,"old_string":...,"new_string":...}

Meaning:

    OpenClaude may include replace_all:false in history.
    The server removes it locally for Edit before re-rendering model-visible prompt history.

### General schema canonicalization

Expected stable result:

    QWEN36_SCHEMA_TOOL_ARGS_CANONICAL_V1 = absent

Meaning:

    No global schema-based tool argument rewriting is active in the stable line.

---

## Common prefix mismatch / full prefill interpretation

Observed pattern:

    COMMON_PREFIX_MISMATCH
    COMMON_PREFIX_MISMATCH_RECURRENT_REPREFILL

Interpretation:

    When a recurrent model detects cache/prompt mismatch, the safer behavior is to clear recurrent/KV/checkpoint/cache-local state for that slot and force clean prefill.

Important performance note:

    Full prefill can happen early when a short initial request/title prompt is followed by the long real OpenClaude prompt.
    This costs latency but is safe.

Observed slow-feeling tasks:

    task 479: 634 generated tokens at ~15.56 tok/s -> ~41.43 s
    task 539: 637 generated tokens at ~15.55 tok/s -> ~41.65 s

Interpretation:

    Those tasks were not slow because of full prefill.
    Prompt eval was small.
    The elapsed time came from long generation turns of ~635 tokens.

Conclusion:

    Do not confuse long decode turns with prefill regression.
    For NP2 concurrent tool-heavy workflows, ~15 tok/s generation is expected.

---

## Performance interpretation

Expected prompt eval:

    Large prompt eval can reach ~1000-1500 tok/s depending on prompt size and cache state.
    Small incremental prompt eval may appear lower due overhead.

Expected NP2 concurrent generation:

    Typical: ~14-16 tok/s per observed mixed tool-heavy run
    Best segments: ~22-27 tok/s
    Slow segments under heavier concurrent/edit workload: ~7-10 tok/s

Final interpretation:

    The final line favors correctness over aggressive reuse.
    Full clean prefill is acceptable when mismatch safety requires it.
    Long generation turns dominate perceived latency more than prefill in many OpenClaude runs.

---

## Production recommendation

Use as stable NP2 multiagent coding baseline:

    Engine:
    qwen36-stable-slot-affinity-flag-default-off

    Template:
    qwen36-stable-aibsu-enhanced-empty-think-items

    Runtime:
    Enable --slot-affinity-by-repo-scope for A/B OpenClaude coding agents.
    Keep prompt cache enabled.
    Keep local Edit canonicalization.
    Keep general schema canonicalization OFF.

Recommended daily command additions:

    --slot-affinity-by-repo-scope
    --chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja
    --chat-template-kwargs '{"preserve_thinking":true}'

Avoid in stable:

    Global schema canonicalization for all tools
    Removing empty think frames asymmetrically
    Disabling prompt cache without a specific diagnostic
    Aggressive nearest checkpoint reuse inside tool/edit regions
    Global KV cache clear as a fix

---

## Experimental branch recommendation

General schema canonicalization may be kept only as an experimental branch:

    General ON + local Edit ON

Use it for:

    A/B/C matrix testing
    Comparing prompt strictness effects
    Testing whether schema-order canonicalization helps non-Edit tools

Do not promote to stable unless it passes multiple A/B runs and shows measurable benefit over local Edit only.

---

## Final conclusion

This line finalizes the transition from hardcoded repo-scope slot affinity to a configurable runtime flag.

Primary validated stable design:

    Minimal intervention.
    Slot affinity configurable and default OFF.
    Local Edit canonicalization retained.
    General schema canonicalization OFF.
    Final Aibsu enhanced empty-think items template active.
    Strict prompts with AST function-name checks required for agent validation.

Main achievement:

    Stable NP2 OpenClaude A/B operation with explicit repo-scope slot isolation available when needed, while keeping upstream-like default behavior when the flag is not enabled.

Main trade-off:

    Safety-first recurrent mismatch handling can force full clean prefill.
    This may cost prefill time, but it avoids contaminated KV/tool-call reuse.

Operational recommendation:

    Use this as the new NP2 daily baseline for Qwen3.6 27B NEO CODE with two OpenClaude coding agents.
    Enable --slot-affinity-by-repo-scope for multiagent coding workflows.
    Keep the final template and local Edit canonicalizer as part of the baseline.
