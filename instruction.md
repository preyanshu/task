You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

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

The visible sample instances are:

```json
{
  "instances": [
    {
      "id": "sample_alpha",
      "n": 8,
      "initial": "00110110",
      "target": "11000101",
      "keys": [
        {"name": "amber", "start": 1, "stop": 4},
        {"name": "cobalt", "start": 5, "stop": 0},
        {"name": "ember", "start": 2, "stop": 7},
        {"name": "jade", "start": 6, "stop": 1},
        {"name": "opal", "start": 0, "stop": 3}
      ]
    },
    {
      "id": "sample_beta",
      "n": 9,
      "initial": "110010011",
      "target": "000110010",
      "keys": [
        {"name": "birch", "start": 0, "stop": 5},
        {"name": "cedar", "start": 4, "stop": 8},
        {"name": "dune", "start": 7, "stop": 2},
        {"name": "iris", "start": 1, "stop": 6},
        {"name": "moss", "start": 3, "stop": 7},
        {"name": "rune", "start": 8, "stop": 4}
      ]
    },
    {
      "id": "sample_gamma",
      "n": 10,
      "initial": "0101110010",
      "target": "1001111111",
      "keys": [
        {"name": "atlas", "start": 9, "stop": 3},
        {"name": "brass", "start": 2, "stop": 6},
        {"name": "coral", "start": 5, "stop": 9},
        {"name": "drift", "start": 1, "stop": 4},
        {"name": "flint", "start": 6, "stop": 0},
        {"name": "lumen", "start": 3, "stop": 8}
      ]
    }
  ]
}
```

Your solver may be tested on additional instances with the same schema. It must print JSON
to stdout with exactly this shape:

```json
{
  "answers": {
    "sample_alpha": "amber+jade",
    "sample_beta": "cedar+dune+moss"
  }
}
```

Include every input instance id exactly once.
