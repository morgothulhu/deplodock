---
mode: agent
description: Run a minimal single-variant deplodock bench smoke test on the local GPU.
---

# Simple benchmark smoke test

Run the smallest possible end-to-end benchmark to confirm the local pipeline works (SSH →
deploy → `vllm bench serve` → results → teardown). This runs **one** variant only, so it is fast
and cheap compared to a full sweep.

## Prerequisites

`bench --local` connects over SSH to `127.0.0.1`. If it fails with "Connection refused" or a
missing identity file, run the `setup-local-ssh-bench` prompt first to create the key and start
`sshd`.

## 1. Free port 8000

A leftover `deploy local` container holds port 8000 and collides with the bench deploy:

```bash
docker rm -f vllm_0 2>/dev/null || true
```

## 2. Run a single variant

Use `--filter` to select exactly one variant (the cheapest: lowest concurrency, smallest
context). The filter is an fnmatch glob over the variant key:

```bash
./venv/bin/deplodock bench recipes/Qwen3-Coder-30B-A3B-Instruct-AWQ \
  --local --filter "engine.llm.max_concurrent_requests=1"
```

Expect a single task in one execution group. If the filter matches more than one variant, narrow
it (e.g. add `--filter "engine.llm.context_length=102400"`).

## 3. Report results

From the SUMMARY, report whether the variant succeeded and the run-directory path. Then show the
key throughput/latency numbers from that run's `*_benchmark.txt` (or `.json`) result file —
request throughput, output token throughput, mean TTFT, and mean TPOT.

If the variant fails, read `benchmark.log` in the run directory, diagnose the cause, and report
it before stopping.
