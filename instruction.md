You are solving Timeline Locks.

The public puzzle instances are in `data/public_instances.json`. Write a solver at
`solution/solve.py`.

Each instance describes a circular timeline with positions numbered `0` through `n - 1`.
The state is a binary string of length `n`. You may activate any subset of the named keys
at most once.

When a key is activated, it performs one clockwise sweep:

1. Put the marker on the key's `start` position.
2. Flip the bit under the marker.
3. Move the marker one position clockwise, wrapping from `n - 1` to `0`.
4. If the marker is now on the key's `stop` position, the sweep is finished and the
   `stop` position is not flipped by that move.
5. Otherwise, repeat from step 2.

The order of activated keys does not matter because every operation is a bit flip.

For each instance, your solver must find the lexicographically smallest answer string
among all subsets that transform `initial` into `target`. An answer string is the selected
key names sorted alphabetically and joined with `+`, such as `amber+jade`. Use `NONE` for
the empty subset.

Your solver is run as:

```bash
python3 solution/solve.py path/to/instances.json
```

It must print JSON to stdout with exactly this shape:

```json
{
  "answers": {
    "sample_alpha": "amber+jade",
    "sample_beta": "cedar+dune+moss"
  }
}
```

Include every public instance id exactly once.
