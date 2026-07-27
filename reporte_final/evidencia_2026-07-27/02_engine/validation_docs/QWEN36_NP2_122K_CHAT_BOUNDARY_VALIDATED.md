# Qwen3.6 27B — ik_llama.cpp np=2 122K Chat-Boundary Checkpoints Validated

## Validation status

Validated.

Branch: qwen36-port-message-spans
Commit: 24f57b585 Add ChatML fallback for server message spans
Tag np=1: qwen36-chat-boundary-checkpoints-np1-validated
Tag np=2: qwen36-np2-122k-chat-boundary-checkpoints-openclaude-parallel-validated

## Stable preset

Model: /home/alcazarjuanc/models/gguf/Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf
Hardware: 2x RTX 4080 SUPER 16GB
Context: -c 122880
Parallel slots: -np 2
Context per slot: 61440
Split: -ts 57,43
Batch: -b 2048
Ubatch: -ub 1024
KV cache: -ctk q8_0 -ctv q8_0
Checkpoints: --ctx-checkpoints 8 --ctx-checkpoints-interval 4096
Prompt cache: enabled

## Server command

cd ~/ai-stack/servers/ik_llama.cpp/build/bin

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
  --ctx-checkpoints 8 \
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
  --chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja \
  --chat-template-kwargs '{"preserve_thinking":true}'

## Validated behavior

np=1 validation: n_before_user=12 and checkpoint created at n_tokens=12.
np=2 validation: OpenClaude Agent A and Agent B ran in parallel successfully.
Agent A: added subtract, multiply, divide; pytest 5/5 passed.
Agent B: added square, cube, mean; pytest 5/5 passed.

## Key evidence

message_spans was active on both slots.
Boundary checkpoints were created exactly at n_before_user values.
COMMON_PREFIX_MISMATCH recovered from boundary checkpoint in about 24.74 ms.
PROMPT_CACHE_LOAD_DROP_EMPTY_RECURRENT continued dropping empty recurrent checkpoints safely.

Representative prompt eval performance: roughly 1370 to 1580 tok/s.
Representative generation under concurrency: roughly 6 to 22 tok/s.

## Do not disable

--jinja
--chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja
--chat-template-kwargs {"preserve_thinking":true}
--ctx-checkpoints 8
--ctx-checkpoints-interval 4096
prompt cache

Do not use -nocb or --cache-ram 0 unless intentionally testing cache-disabled behavior.

## Next improvement candidates

1. Test np=3 using this same branch.
2. Adapt better checkpoint retention policy similar to llama.cpp PR #22826.
3. Consider checkpointing every user boundary, not only the last user boundary.
4. Reduce message_spans logs after validation.

## Refinement: skip ordinary checkpoints before chat boundary

Validated commit: cf595b858 Skip interval checkpoints before chat boundary

Validated tag: qwen36-np2-122k-boundary-skip-ordinary-checkpoints-validated

This refinement improves the previous chat-boundary checkpoint implementation by preventing ordinary prompt checkpoints before a known user-message boundary is reached.

Behavior:

- If n_before_user is known and still pending, skip ordinary prompt-tail checkpoints.
- If n_before_user is known and still pending, skip interval checkpoints.
- Create the first semantic checkpoint exactly at n_before_user.
- After the boundary checkpoint is created, normal prompt-tail or interval checkpointing can continue.

Validation result:

- np=1 remained valid: n_before_user=12 produced checkpoint at n_tokens=12.
- np=2 / 122K OpenClaude parallel validation succeeded.
- Agent A completed code edits and pytest 5/5 passed.
- Agent B completed code edits and pytest 5/5 passed.
- COMMON_PREFIX_MISMATCH restored from boundary checkpoint in about 27.42 ms.
- Prompt eval remained strong, commonly around 1430-1617 tok/s on large prompts.

This is now the preferred baseline over 24f57b585 for np=2 OpenClaude parallel coding workloads.
