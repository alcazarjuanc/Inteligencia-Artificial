# Final Successful Benchmark

Date: 2026-07-27

## Inference configuration

- Model: Qwopus3.6-27B-Coder-Q6_K
- Engine: ik_llama.cpp
- Agent harness: OpenClaude
- GPUs used for final successful run: 2x RTX 4080 SUPER
- RTX 5070 Ti excluded from inference
- Parallel agents: 2
- Total context: 131072
- Context per slot: 65536
- Tensor split: 57,43
- KV cache: q8_0
- Flash Attention: enabled
- Reasoning: disabled
- Repo-scope slot affinity: enabled
- Context checkpoints: 16
- Checkpoint interval: 4096

## Agent A

Task:
CSV ingestion and preprocessing utilities.

Final result:

- 8/8 pytest tests passed
- No recovery required
- Final status: FULL PASS

## Agent C

Task:
Machine-learning pipeline using pandas and scikit-learn.

Execution:

- Initial pytest execution failed
- Agent changed diagnostic strategy
- First failure was inspected
- Missing pandas import in test file was identified
- Targeted correction was applied
- pytest was executed again

Final result:

- 8/8 pytest tests passed
- Autonomous recovery demonstrated
- Final status: FULL PASS AFTER RECOVERY

## Aggregate

- Agent A: 8/8 PASS
- Agent C: 8/8 PASS
- Total: 16/16 PASS
- Two OpenClaude agents executed concurrently
- Final run completed without system crash
