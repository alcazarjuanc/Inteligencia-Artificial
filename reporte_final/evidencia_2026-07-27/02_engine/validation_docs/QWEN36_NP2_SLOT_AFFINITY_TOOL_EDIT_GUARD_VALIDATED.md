# Qwen3.6 NP2 Slot Affinity + Tool/Edit Guard Validated

## Validated C++ line

Branch:

```text
qwen36-slot-affinity-from-message-spans-partial-v1
```

Commit:

```text
bae6c70cf Guard partial reprefill on tool edit mismatches
```

Tag:

```text
qwen36-np2-slot-affinity-tool-edit-guard-validated
```

Base parent:

```text
f65bf3392 Add minimal message spans partial reprefill
```

Previous stable parent line:

```text
c96c4e21e Guard recurrent prompt cache reuse on mismatch
```

This line builds on the previous recurrent mismatch safety work and adds a stricter NP2 multiagent guard for tool/edit contamination.

---

## Validated external chat template

Template snapshot:

```text
~/ai-stack/templates/qwen3.6/chat_template.qwen36-np2-slot-affinity-tool-edit-guard-validated.jinja
```

SHA256:

```text
833928e63338f8aa2b791b26bc99ad1c2523d9d688c5c706d044702127bc913d
```

Required active template features:

```text
QWEN36_STABLE_EMPTY_THINK_FRAME_V1
QWEN36_CANONICAL_TOOL_ARG_ORDER_V1
```

Rejected / removed template feature:

```text
QWEN36_NO_EMPTY_THINK_FRAME_V2
```

The validated template keeps assistant history and generation prefill symmetric when reasoning is disabled. This is required because Qwen3.6/OpenClaude still carries the empty think frame in cache/KV history. Removing it from only one side causes prompt/cache mismatch.

---

## Validated runtime preset

Model:

```text
~/models/gguf/Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf
```

Validated command:

```bash
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
  --chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.qwen36-np2-slot-affinity-tool-edit-guard-validated.jinja \
  --chat-template-kwargs '{"preserve_thinking":true}'
```

Runtime interpretation:

```text
Total context: 122880
Parallel slots: 2
Effective context per slot: 61440
GPU split: 57,43
Batch: 2048
Ubatch: 1024
Checkpoints: 16
Checkpoint interval: 4096
Prompt cache: enabled
Reasoning: disabled
Reasoning tokens: none
Template: validated external Qwen3.6 snapshot
```

---

## Validated hardware

Validated on:

```text
2x NVIDIA GeForce RTX 4080 SUPER
Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf
ik_llama.cpp
OpenClaude local agents
```

Expected VRAM behavior during NP2 validation:

```text
GPU0: roughly 14.4-15.0 GiB used
GPU1: roughly 13.0-15.1 GiB used depending on checkpoint/cache state
```

GPU1 may report less or more depending on display load, slot assignment, checkpoint count, cache state, and whether the run is in a full clean prefill region or a lighter cached region.

---

## Validated behavior

Validated with two parallel OpenClaude agents:

```text
Agent A: oc-agent-a-benchmark, math task
Agent B: oc-agent-b-benchmark, string task
```

Final validation result:

```text
Agent A: 21 passed, no forbidden functions
Agent B: 21 passed, no forbidden functions
```

Observed final user-visible behavior:

```text
No visible functional contamination.
Both agents completed their own task.
No cross-agent function leakage in final files.
No forbidden functions detected.
```

This validation is important because previous lines could sometimes finish but still show semantic contamination, tool-call corruption, wrong file paths, or old_string/new_string drift.

---

## Problem this line solves

The previous bad pattern was:

```text
COMMON_PREFIX_MISMATCH
-> restored context checkpoint
-> partial reuse near tool/edit region
-> contaminated KV/tool-call state
-> wrong old_string/new_string continuation
-> cross-agent or cross-tool corruption
```

The validated corrected pattern is:

```text
COMMON_PREFIX_MISMATCH
-> detect unsafe tool/edit mismatch region
-> skip partial reprefill
-> COMMON_PREFIX_MISMATCH_RECURRENT_REPREFILL
-> full clean prefill
-> request completes safely
```

The cost is extra prefill, but the benefit is avoiding contaminated KV reuse inside tool calls.

---

## Key fixes included

### 1. Message span safe boundaries

This line keeps the message span work from the previous stable fallback line.

Safe checkpoints are created at:

```text
user_start
user_end
```

Checkpoint metadata distinguishes:

```text
safe_boundary=1
type=user_start/user_end
source=message_spans
```

Interpretation:

```text
user_start and user_end are safe semantic boundaries.
They are safer than arbitrary prompt-tail offsets.
They provide stable anchor points for recurrent checkpointing.
```

This replaces the previous idea of relying on prompt-tail checkpoint offsets as the main boundary mechanism.

---

### 2. Minimal checkpoint metadata

Checkpoints now carry enough metadata to distinguish safe message boundaries from ordinary/recurrent checkpoints.

Important metadata concepts:

```text
safe_boundary
checkpoint_type
checkpoint_source
n_tokens
```

Important checkpoint types:

```text
user_start
user_end
recurrent/base interval checkpoint
```

Interpretation:

```text
user_start/user_end checkpoints are safe boundaries.
Base/recurrent checkpoints can still exist, but are not automatically considered safe semantic boundaries.
```

---

### 3. Strict slot affinity

Strict slot affinity maps repo/task scope to a minimal key:

```text
agent-a -> a
agent-b -> b
agent-c -> c
```

Observed behavior:

```text
SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1
reason=init
reason=match
reason=busy
reason=no_slot
```

Interpretation:

```text
Agent A should keep returning to the slot that owns key=a.
Agent B should keep returning to the slot that owns key=b.
If the matching slot is busy, the request is deferred instead of being assigned to the wrong slot.
```

This reduces cross-agent cache contamination.

Important note:

```text
Slot affinity does not solve tool-call serialization mismatch by itself.
It prevents cross-agent slot reuse, but tool/edit regions can still mismatch inside the correct slot.
```

---

### 4. Stable empty-think symmetry

The validated template intentionally keeps the empty think frame when thinking is disabled:

```text
<|im_start|>assistant
<think>

</think>
```

Reason:

```text
The cache/KV side already contains the empty think frame.
Removing it only from the reconstructed prompt causes cache/prompt mismatch.
```

Rejected approach:

```text
QWEN36_NO_EMPTY_THINK_FRAME_V2
```

Why it was rejected:

```text
It removed the empty think frame from the prompt side, but the cache still contained those tokens.
This made COMMON_PREFIX_MISMATCH worse or moved the mismatch to a different layer.
```

Current accepted approach:

```text
Symmetry over aesthetics.
Do not remove <think></think> unless both cache and prompt serialization are changed symmetrically.
```

---

### 5. Canonical tool argument order

The validated template renders tool call arguments with stable key order:

```jinja
dictsort
```

Feature marker:

```text
QWEN36_CANONICAL_TOOL_ARG_ORDER_V1
```

Reason:

```text
Tool-call argument order drift can create prompt/cache mismatch even if the semantic content is the same.
Stable serialization reduces artificial mismatch.
```

This helps with tool calls but does not fully solve old_string/new_string mismatch by itself.

---

### 6. Tool/edit mismatch guard

Feature marker:

```text
QWEN36_SKIP_PARTIAL_ON_TOOL_EDIT_MISMATCH_V1
```

When COMMON_PREFIX_MISMATCH occurs inside tool/edit regions, partial reprefill is skipped.

Detected unsafe regions include:

```text
<tool_call>
</tool_call>
<function=
</function>
<parameter=
</parameter>
old_string
new_string
replace_all
file_path
Update(
Edit(
Write(
```

Expected safe log pattern:

```text
COMMON_PREFIX_MISMATCH_SKIP_PARTIAL_TOOL_EDIT_V1
COMMON_PREFIX_MISMATCH_RECURRENT_REPREFILL
```

Meaning:

```text
Do not partial-reuse contaminated tool/edit KV.
Force full clean prefill.
```

This is the core stabilization improvement of this line.

---

## Why tool/edit regions are unsafe for partial reprefill

The observed bad mismatch pattern was:

```text
cache:
<parameter=old_string>
...
</parameter>
<parameter=new_string

prompt:
<parameter=new_string>
...
```

or:

```text
cache:
<parameter=old_string>
def subtract(a, b):
    return a - b

prompt:
<parameter=new_string>
def subtract(a, b):
    return a -
```

This means the cache and prompt disagree about where the tool edit payload lives.

In this state, partial reuse is unsafe because the KV may continue from the wrong parameter context.

Correct response:

```text
Skip partial.
Clear local recurrent/KV/checkpoint/cache state for the affected slot.
Force full clean prefill.
```

---

## Partial reprefill policy

Validated policy:

```text
If mismatch is outside unsafe tool/edit regions:
  partial reprefill may be used.

If mismatch is inside unsafe tool/edit regions:
  skip partial reprefill.
  force full clean prefill.
```

For NP2/NP3 multiagent use:

```text
Do not use aggressive nearest-checkpoint reuse inside tool/edit regions.
Do not restore arbitrary checkpoints near old_string/new_string.
Prefer clean prefill when the mismatch is inside tool serialization.
```

For NP1:

```text
Nearest checkpoint reuse may be safer than NP2/NP3, but this should still be validated separately.
The current validated line is NP2.
```

---

## Prompt cache policy

Prompt cache remains enabled in this NP2 line.

Do not use:

```text
--cache-ram 0
```

for this validated NP2 baseline unless specifically running a diagnostic comparison.

Reason:

```text
Prompt cache is part of the validated NP2 workflow.
The current fix does not require disabling prompt cache.
The safety wall is the tool/edit mismatch guard plus recurrent mismatch clean prefill.
```

---

## Expected logs

Expected healthy slot affinity logs:

```text
SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=a slot=0 action=select reason=init
SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=a slot=0 action=select reason=match
SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=b slot=1 action=select reason=init
SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1: task=<id> key=b slot=1 action=select reason=match
```

Expected healthy tool/edit guard logs:

```text
COMMON_PREFIX_MISMATCH_SKIP_PARTIAL_TOOL_EDIT_V1
COMMON_PREFIX_MISMATCH_RECURRENT_REPREFILL
```

Expected interpretation:

```text
The mismatch landed inside an unsafe tool/edit region.
Partial reuse was rejected.
The slot was cleaned and prefilling restarted safely.
```

Expected final outcome:

```text
No restored contaminated checkpoint inside tool/edit region.
No visible function leakage.
No wrong old_string/new_string continuation.
No final forbidden functions.
```

---

## Performance observed in validation

Large prompt eval:

```text
~950-1475 tok/s
```

Typical generation under NP2 concurrency:

```text
~10-15 tok/s
```

Best observed generation segments:

```text
~22-27 tok/s
```

Slowest observed generation segments under heavier concurrent/edit workload:

```text
~7-10 tok/s
```

Tool/edit mismatch full prefill cost:

```text
~5K-7.5K tokens re-prefill
```

Interpretation:

```text
The guard costs speed when mismatches occur inside tool/edit regions.
That cost is acceptable because it prevents contaminated partial reuse.
Prompt eval remains strong enough on 2x RTX 4080 SUPER.
```

---

## What improved compared with previous attempts

### Before

```text
COMMON_PREFIX_MISMATCH could restore a nearby checkpoint.
Nearest checkpoint reuse could land inside a tool call.
old_string/new_string could drift.
Agents could contaminate each other or corrupt tool arguments.
```

### Now

```text
Slot affinity keeps agents tied to their own slots.
Empty-think symmetry reduces reasoning-frame mismatch.
Canonical dictsort reduces tool argument order mismatch.
Tool/edit guard blocks partial reuse in unsafe regions.
Full clean prefill is used when needed.
```

---

## Validated final result

The final NP2 A/B validation completed successfully:

```text
Agent A:
21 passed
No forbidden functions

Agent B:
21 passed
No forbidden functions
```

Interpretation:

```text
No visible final contamination.
The tool/edit mismatch guard behaved correctly.
The line is suitable as a daily NP2 coding-agent baseline.
```

---

## Recommended daily use

Use this line for:

```text
Daily NP2 multiagent coding baseline.
Two parallel OpenClaude coding agents.
Tool-heavy workflows where correctness matters more than aggressive partial reuse.
```

Recommended:

```text
-c 122880
-np 2
n_ctx_slot = 61440
--ctx-checkpoints 16
--ctx-checkpoints-interval 4096
prompt cache enabled
validated external Qwen3.6 template snapshot
```

Avoid:

```text
Aggressive nearest checkpoint restore inside tool/edit regions.
Removing empty think frames asymmetrically.
Disabling prompt cache unless running a specific diagnostic.
Using global KV cache clear as a fix.
```

---

## Notes for future NP3 work

This commit is validated as NP2.

For NP3:

```text
Re-test separately.
Do not assume NP2 validation automatically transfers to NP3.
NP3 introduces more slot pressure, more concurrent tool-call traffic, and more opportunities for tool/edit mismatch.
```

Likely NP3 requirements:

```text
Slot affinity remains required.
Tool/edit mismatch guard remains required.
Prompt cache scope guard remains required.
Recurrent mismatch clean prefill remains required.
Do not use global kv_cache_clear.
Prefer per-slot / per-sequence cleanup if deeper KV cleanup is needed.
```

If testing NP3:

```text
Use separate branch.
Use explicit A/B/C repos.
Track which agent stalls.
Inspect model log for old_string/new_string, file_path, <parameter>, and malformed tool-call loops.
```

---

## Do not remove

Keep:

```text
SLOT_AFFINITY_BY_REPO_SCOPE_STRICT_V1
QWEN36_STABLE_EMPTY_THINK_FRAME_V1
QWEN36_CANONICAL_TOOL_ARG_ORDER_V1
QWEN36_SKIP_PARTIAL_ON_TOOL_EDIT_MISMATCH_V1
COMMON_PREFIX_MISMATCH_RECURRENT_REPREFILL
PROMPT_CACHE_LOAD_SKIP_RECURRENT_SLOT_CHECKPOINTS
PROMPT_CACHE_LOAD_DROP_EMPTY_RECURRENT
```

Reason:

```text
Each one protects a different failure mode.
Removing one may make the system appear faster while reintroducing contamination.
```

---

## Final conclusion

This line is the current validated NP2 stable baseline for Qwen3.6 27B NEO CODE with OpenClaude A/B coding agents on 2x RTX 4080 SUPER.

Primary achievement:

```text
Stable multiagent NP2 operation with reduced tool-call contamination.
```

Main trade-off:

```text
Full clean prefill is forced when COMMON_PREFIX_MISMATCH happens inside unsafe tool/edit regions.
This is slower than partial reuse but safer.
```

Operational recommendation:

```text
Use this as the daily NP2 baseline.
Prefer stability over aggressive partial reuse.
Do not enable nearest checkpoint reuse inside tool/edit regions.
Do not remove empty think frames unless cache and prompt serialization are changed symmetrically.
```
