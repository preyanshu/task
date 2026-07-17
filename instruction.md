# Relay-lock repair

`/app/solve.py` is a Python 3 relay-lock solver. It is supposed to be invoked as:

```text
python3 /app/solve.py <level.json> <output.json>
```

The input is one documented relay-lock level. It must write exactly `{"commands":[...]}` to the output path. The program will be run on other levels with the same schema, not only the public examples.

Each level contains a one-dimensional device, a player position, a crate position, a dial orientation, a key position, ice cells, a conveyor cell, a plate, a goal, and target conditions. The available commands are `move east`, `move west`, `turn clockwise`, `turn counterclockwise`, `push east`, `take key`, `use key`, and `wait`. `/app/RELAYLOCK.md` is complete and self-contained: it fully defines every legal state transition, and the public examples are illustrative only.

The verifier replays your commands independently. It rejects illegal commands and unsolved levels. Among solving transcripts it requires the canonical optimum: minimum command count, then minimum pushes, then minimum ice-wear, then lexicographically smallest command list. It recomputes that canonical answer independently, so each hidden level has one unique accepted transcript. Public examples are in `/app/levels_public.json`; together they exercise every documented mechanic at least once, but they are not the source of truth. Do not hard-code their answers. Use only the Python standard library.

Run the public tests with:

```text
cd /app && python3 run_tests.py
```

Fix any bug(s) you find. You may modify `/app/solve.py`. Do not modify `/app/RELAYLOCK.md`, `/app/levels_public.json`, or `/app/run_tests.py`. The final program must be deterministic, accept arbitrary valid level JSON in this schema, and write no files other than the requested output.

You have 900 seconds. Do not use online solutions or hints.
