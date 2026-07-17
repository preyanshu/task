You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

Each instance describes a circular timeline with positions numbered `0` through `n - 1`.
The state is a binary string of length `n`. Several named markers stand on positions of
the timeline. Every marker also has a `moves` string made of `L`, `R`, and `S`.

Simulate exactly `ticks` ticks. On tick `t`, marker `m` uses
`m["moves"][t % len(m["moves"])]`.

Each tick has two phases:

1. Proposal phase: using only marker positions from the start of this tick, every marker
   proposes a destination. `L` means one position counter-clockwise, `R` means one
   position clockwise, and `S` means the marker's current position.
2. Commit phase: group proposals by destination. A marker whose proposed destination was
   proposed by two or more markers is blocked: it stays where it started the tick and
   flips the bit at that starting position. A marker whose proposed destination is unique
   moves to that destination and flips the bit at that destination.

Only equal proposed destinations cause blocking.

For each input instance, output the final binary state after all ticks.

The visible sample instances are:

```json
{
  "instances": [
    {
      "id": "sample_copper",
      "n": 8,
      "initial": "10111111",
      "ticks": 5,
      "tokens": [
        {"name": "a", "pos": 1, "moves": "SRSLS"},
        {"name": "b", "pos": 0, "moves": "RSLRS"},
        {"name": "c", "pos": 7, "moves": "SLLSS"}
      ]
    },
    {
      "id": "sample_quartz",
      "n": 9,
      "initial": "111101101",
      "ticks": 5,
      "tokens": [
        {"name": "a", "pos": 5, "moves": "SSSSL"},
        {"name": "b", "pos": 2, "moves": "SSLSR"},
        {"name": "c", "pos": 6, "moves": "LSSSS"}
      ]
    },
    {
      "id": "sample_onyx",
      "n": 10,
      "initial": "0011111010",
      "ticks": 6,
      "tokens": [
        {"name": "a", "pos": 4, "moves": "SSSSSL"},
        {"name": "b", "pos": 7, "moves": "LRSRSR"},
        {"name": "c", "pos": 0, "moves": "SRSLLS"}
      ]
    }
  ]
}
```

For these visible samples, the expected answers are:

```json
{
  "answers": {
    "sample_copper": "11111001",
    "sample_quartz": "110111001",
    "sample_onyx": "0010010000"
  }
}
```

Your solver is run as:

```bash
python3 solution/solve.py path/to/instances.json
```

It must print JSON to stdout with exactly this shape:

```json
{
  "answers": {
    "sample_copper": "11111001"
  }
}
```

Include every input instance id exactly once.
