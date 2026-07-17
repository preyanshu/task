You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

Each instance has named lock bits and named chants. The lock order in the input is also
the order of bits in `initial` and `target`.

Each chant has a `scroll` string and a list of motifs. A motif names one lock and a
string `pattern`.

When a chant is activated, count how many starting positions in the chant's scroll match
each motif. A start position matches a motif when that motif's pattern starts there.
Count by starting position: if the same motif matches at several positions, every start
position counts. Work through the motif list for the chant; if a motif's count is odd,
flip its named lock once, and if the count is even, do not flip that lock for that motif.

You may activate any subset of chants at most once. The selected chants are activated in
alphabetical order by chant name.

For each input instance, find the lexicographically smallest answer string among all
chant subsets that transform `initial` into `target`. An answer string is the selected
chant names sorted alphabetically and joined with `+`, such as `ash+cove`. Use `NONE` for
the empty subset.

The visible sample instances are:

```json
{
  "instances": [
    {
      "id": "sample_amber",
      "initial": "0101",
      "target": "0010",
      "locks": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
      "chants": [
        {"name": "iris", "scroll": "abxcdab", "motifs": [{"lock": "A", "pattern": "ab"}, {"lock": "C", "pattern": "xcd"}]},
        {"name": "jade", "scroll": "tornet", "motifs": [{"lock": "B", "pattern": "to"}, {"lock": "D", "pattern": "net"}]},
        {"name": "kilo", "scroll": "mistral", "motifs": [{"lock": "A", "pattern": "mi"}, {"lock": "D", "pattern": "al"}]},
        {"name": "lumen", "scroll": "redblue", "motifs": [{"lock": "B", "pattern": "red"}, {"lock": "C", "pattern": "blue"}]}
      ]
    },
    {
      "id": "sample_brass",
      "initial": "10010",
      "target": "10110",
      "locks": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}, {"name": "E"}],
      "chants": [
        {"name": "ash", "scroll": "catdogcat", "motifs": [{"lock": "A", "pattern": "cat"}, {"lock": "B", "pattern": "dog"}]},
        {"name": "bryn", "scroll": "sun-moon", "motifs": [{"lock": "C", "pattern": "sun"}, {"lock": "E", "pattern": "moon"}]},
        {"name": "cove", "scroll": "riverstone", "motifs": [{"lock": "B", "pattern": "river"}, {"lock": "D", "pattern": "stone"}]},
        {"name": "dune", "scroll": "northstar", "motifs": [{"lock": "A", "pattern": "north"}, {"lock": "E", "pattern": "star"}]},
        {"name": "elm", "scroll": "glasswind", "motifs": [{"lock": "C", "pattern": "glass"}, {"lock": "D", "pattern": "wind"}]}
      ]
    }
  ]
}
```

For these visible samples, the expected answers are:

```json
{
  "answers": {
    "sample_amber": "iris+jade",
    "sample_brass": "ash+cove+elm"
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
    "sample_amber": "iris+jade"
  }
}
```

Include every input instance id exactly once.
