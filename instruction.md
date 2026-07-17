You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

Each instance describes locks arranged around a circular timeline and named routes that
may be activated. The order of locks in `locks` is clockwise order around the circle and
is also the bit order used by `initial` and `target`.

Each route has a `from` lock and a `to` lock. When a route is activated, it starts on
the `from` lock and flips that lock. It then repeatedly advances one lock clockwise,
flipping each lock it visits. The route stops when it reaches the next visit to `to`
after it has left `from`.

You may activate any subset of routes at most once. Selected routes are activated in
alphabetical order by route name.

For each input instance, find the lexicographically smallest answer string among all
route subsets that transform `initial` into `target`. An answer string is the selected
route names sorted alphabetically and joined with `+`, such as `ash+cove`. Use `NONE`
for the empty subset.

The visible sample instances are:

```json
{
  "instances": [
    {
      "id": "sample_amber",
      "initial": "00000",
      "target": "11100",
      "locks": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}, {"name": "E"}],
      "routes": [
        {"name": "iris", "from": "A", "to": "C"},
        {"name": "jade", "from": "B", "to": "D"},
        {"name": "kilo", "from": "D", "to": "E"},
        {"name": "lumen", "from": "E", "to": "B"}
      ]
    },
    {
      "id": "sample_brass",
      "initial": "101010",
      "target": "000110",
      "locks": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}, {"name": "E"}, {"name": "F"}],
      "routes": [
        {"name": "ash", "from": "A", "to": "B"},
        {"name": "bryn", "from": "C", "to": "E"},
        {"name": "cove", "from": "B", "to": "D"},
        {"name": "dune", "from": "E", "to": "F"},
        {"name": "elm", "from": "F", "to": "B"}
      ]
    }
  ]
}
```

For these visible samples, the expected answers are:

```json
{
  "answers": {
    "sample_amber": "iris",
    "sample_brass": "ash+cove"
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
    "sample_amber": "iris"
  }
}
```

Include every input instance id exactly once.
