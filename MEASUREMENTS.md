# Measurement Log

## 2026-07-18 02:03 Harbor run: hidden list-pattern motif variant

Command:

```bash
harbor run --agent codex --model gpt-5.4 --path /home/preyanshu/Downloads/fix-task-broken --task timeline-locks -k 4 --ae CODEX_AUTH_JSON_PATH="$CODEX_AUTH_JSON_PATH" -y
```

Result: 4/4 passed, mean reward 1.000, no exceptions.

Transcript notes:
- `timeline-locks__2SCQPcf` implemented list-pattern handling and added an explicit list-pattern edge case before final answer.
- `timeline-locks__EMStsST` implemented list-pattern handling and ran randomized brute-force checks.
- `timeline-locks__tRbzKs2` handled the main motif-count logic and passed; no clean hidden-only failure.
- `timeline-locks__XU5TcuC` handled alternative patterns and passed.

Diagnosis: disqualified as a stump. The optional list shape was too visible in the written rule, and capable agents implemented it directly rather than building a main-case-only solution.

## 2026-07-18 02:13 Harbor run: duplicate motif lock flips

Command:

```bash
harbor run --agent codex --model gpt-5.4 --path /home/preyanshu/Downloads/fix-task-broken --task timeline-locks -k 4 --ae CODEX_AUTH_JSON_PATH="$CODEX_AUTH_JSON_PATH" -y
```

Result: 4/4 passed, mean reward 1.000, no exceptions.

Transcript notes:
- Completed solvers used XOR for each odd motif, e.g. `effect ^= 1 << lock_index[...]`, which correctly cancels two odd motifs naming the same lock.
- At least two runs also added extra reasoning around lexicographic reconstruction and zero-delta edge cases.

Diagnosis: disqualified as a stump. The "flip" wording was clear enough that agents naturally implemented repeated flips rather than the intended OR shortcut.
