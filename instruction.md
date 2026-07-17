You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

Each instance describes a small grid of named islands and named beams. Every island has
one grid cell and one binary lock bit. The island order in the input is also the order of
bits in `initial` and `target`.

You may activate any subset of beams at most once. The selected beams are activated in
alphabetical order by beam name. A beam has an ordered `path` of grid cells. When the
beam visits an island cell, that island's bit flips. If the bit just became `0`, that
beam activation ends immediately; otherwise the beam continues to the next path cell.
Water cells are ignored.

For each input instance, find the smallest answer string among all beam subsets that
transform `initial` into `target`. An answer string is the selected beam names sorted
alphabetically and joined with `+`, such as `ash+cove`. Use `NONE` for the empty subset.

Answer strings are compared character by character. The default character order is
`abcdefghijklmnopqrstuvwxyz+`; an instance may include `dial`, which is the character
order for that instance. If `NONE` is a valid answer, treat it as larger than every
non-empty answer string.

The visible sample instances are:

```json
{
  "instances": [
    {
      "id": "sample_amber",
      "initial": "00000",
      "target": "11001",
      "islands": [
        {"name": "A", "cell": [0, 0]},
        {"name": "B", "cell": [0, 1]},
        {"name": "C", "cell": [0, 2]},
        {"name": "D", "cell": [1, 0]},
        {"name": "E", "cell": [1, 1]}
      ],
      "beams": [
        {"name": "iris", "path": [[0, 0], [0, 1]]},
        {"name": "jade", "path": [[0, 2], [1, 0]]},
        {"name": "kilo", "path": [[1, 1]]},
        {"name": "lumen", "path": [[0, 0], [1, 1]]},
        {"name": "moss", "path": [[0, 1], [1, 0]]}
      ]
    },
    {
      "id": "sample_brass",
      "initial": "000000",
      "target": "110011",
      "islands": [
        {"name": "A", "cell": [0, 0]},
        {"name": "B", "cell": [0, 1]},
        {"name": "C", "cell": [0, 2]},
        {"name": "D", "cell": [1, 0]},
        {"name": "E", "cell": [1, 1]},
        {"name": "F", "cell": [1, 2]}
      ],
      "beams": [
        {"name": "ash", "path": [[0, 0], [0, 1]]},
        {"name": "bryn", "path": [[0, 2], [1, 0]]},
        {"name": "cove", "path": [[1, 1], [1, 2]]},
        {"name": "dune", "path": [[0, 0], [1, 2]]},
        {"name": "elm", "path": [[0, 1], [1, 0], [1, 1]]}
      ]
    }
  ]
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
    "sample_amber": "iris+kilo"
  }
}
```

Include every input instance id exactly once.
