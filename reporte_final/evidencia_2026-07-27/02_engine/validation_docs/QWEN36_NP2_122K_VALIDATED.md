# Qwen3.6 27B NEO CODE — NP2 122K Validated Preset

## Final validated tag

qwen36-np2-cb-122k-checkpoints8-4096-final-documented-validated

## Final validated commits

0e9d780ef Clarify Qwen3Next recurrent-safe ubatch split log
84b37b0f5 Drop empty recurrent prompt-cache checkpoints
9e387b0c6 Add validated Qwen3.6 np2 122k checkpoint launcher
55e921d91 Add initial recurrent-safe batching guards for Qwen3Next

## Final launcher

scripts/start-qwen36-27b-code-np2-122k-checkpoints8-4096.sh

## Validated server preset

Model:
~/models/gguf/Qwen3.6-27B-NEO-CODE-2T-OT-Q6_K.gguf

Core flags:
--host 0.0.0.0
--port 8080
-sm graph
--max-gpu 2
-ts 57,43
-ngl 999
--flash-attn on
-ctk q8_0
-ctv q8_0
-c 122880
-np 2
-b 2048
-ub 1024
--ctx-checkpoints 8
--ctx-checkpoints-interval 4096
--slot-prompt-similarity 0.3
--threads 16
--threads-batch 24
--temp 0.6
--top-p 0.95
--top-k 20
--min-p 0.0
--presence-penalty 0.0
--repeat-penalty 1.05
--scheduler_async
--reasoning off
--reasoning-tokens none
--jinja
--chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja
--chat-template-kwargs '{"preserve_thinking":true}'

## Validated behavior

- Two OpenClaude agents work in parallel with -np 2.
- Best validated checkpoint setting: --ctx-checkpoints 8 --ctx-checkpoints-interval 4096.
- --slot-prompt-similarity 0.3 remains the validated value.
- --reasoning-tokens none remains part of the stable preset.
- Prompt cache remains enabled.
- -nocb is not used.
- --cache-ram 0 is not used.

## Validated fix

For recurrent/hybrid models, if prompt cache loads:

loaded_tokens=0
loaded_checkpoints>0

then loaded checkpoints are dropped immediately.

Expected log:

PROMPT_CACHE_LOAD_DROP_EMPTY_RECURRENT

## Mixed-sequence ubatch split interpretation

The recurrent-safe mixed-sequence split is expected behavior, not a fatal error.

Old log:

qwen3next mixed-sequence batch contains repeated seq_id values; using single-sequence chunking

New log:

qwen3next recurrent-safe ubatch split active for mixed sequence batch

Meaning:

- The internal ubatch contains mixed sequence IDs.
- Qwen3Next recurrent state needs safe contiguous sequence processing.
- The loop splits the ubatch internally and continues processing the remaining tokens.
- This should not be treated as serialization or a failed parallel run by itself.

## Discarded experiments

Do not restore these unless specifically retesting:

SERVER_RECURRENT_BATCH_SPLIT
SERVER_RECURRENT_SKIP_CROSS_SEQ_PROMPT

Reason:

- SERVER_RECURRENT_BATCH_SPLIT avoided the internal fallback but caused agent stalls.
- SERVER_RECURRENT_SKIP_CROSS_SEQ_PROMPT avoided cross-slot prompt append but serialized the agents.
- The internal src/llama.cpp recurrent-safe ubatch split preserves scheduling better than server-side guards.

## Final interpretation

Keep server batching behavior.
Keep internal recurrent-safe ubatch split.
Keep prompt cache enabled.
Drop only empty recurrent prompt-cache checkpoints.
