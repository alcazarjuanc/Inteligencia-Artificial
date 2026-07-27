#!/usr/bin/env bash

cd ~/ai-stack/servers/ik_llama.cpp/build-mixed-ada-blackwell/bin

CUDA_VISIBLE_DEVICES=0,1 ./llama-server \
  -m ~/models/gguf/Qwopus3.6-27B-Coder-Q6_K.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -sm graph \
  --max-gpu 2 \
  -ts 57,43 \
  -ngl 999 \
  --flash-attn on \
  -ctk q8_0 \
  -ctv q8_0 \
  -c 131072 \
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
  --repeat-penalty 1.05 \
  --scheduler_async \
  --reasoning off \
  --reasoning-tokens none \
  --jinja \
  --chat-template-file ~/ai-stack/templates/qwen3.6/chat_template.jinja \
  --chat-template-kwargs '{"preserve_thinking":true}'
