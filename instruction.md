You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

Each instance describes a small grid of named islands and named beams. Every island has
one or more grid cells and one binary lock bit. The island order in the input is also the
order of bits in `initial` and `target`. Grid cells not listed in any island are water.

You may activate any subset of beams at most once. A beam has an ordered `path` of grid
cells. Read the path from left to right. Whenever the beam enters an island from water or
from a different island, that island flips once. Consecutive path cells in the same
island are still one stay inside that island, not a new entry.

For each input instance, find the lexicographically smallest answer string among all
beam subsets that transform `initial` into `target`. An answer string is the selected
beam names sorted alphabetically and joined with `+`, such as `ash+cove`. Use `NONE` for
the empty subset.

The visible sample instances are:

```json
{
  "instances": [
    {
      "id": "sample_amber",
      "initial": "01001",
      "target": "11100",
      "islands": [
        {"name": "A", "cells": [[0, 0], [0, 1]]},
        {"name": "B", "cells": [[1, 0]]},
        {"name": "C", "cells": [[1, 2], [2, 2]]},
        {"name": "D", "cells": [[2, 0]]},
        {"name": "E", "cells": [[3, 1]]}
      ],
      "beams": [
        {"name": "iris", "path": [[0, 0], [0, 1], [0, 2], [1, 2], [2, 2]]},
        {"name": "jade", "path": [[1, 0], [1, 1], [2, 0]]},
        {"name": "kilo", "path": [[3, 1]]},
        {"name": "lumen", "path": [[0, 0], [1, 0], [2, 0]]},
        {"name": "moss", "path": [[1, 2], [2, 2], [3, 2], [3, 1]]}
      ]
    },
    {
      "id": "sample_brass",
      "initial": "101100",
      "target": "010001",
      "islands": [
        {"name": "A", "cells": [[0, 0]]},
        {"name": "B", "cells": [[0, 2], [1, 2]]},
        {"name": "C", "cells": [[1, 0]]},
        {"name": "D", "cells": [[2, 1]]},
        {"name": "E", "cells": [[3, 0], [3, 1]]},
        {"name": "F", "cells": [[3, 3]]}
      ],
      "beams": [
        {"name": "ash", "path": [[0, 0], [0, 1], [0, 2], [1, 2]]},
        {"name": "bryn", "path": [[1, 0], [2, 0], [2, 1]]},
        {"name": "cove", "path": [[3, 0], [3, 1], [3, 2], [3, 3]]},
        {"name": "dune", "path": [[0, 2], [1, 2], [2, 2], [3, 3]]},
        {"name": "elm", "path": [[1, 0], [2, 1], [3, 1]]}
      ]
    }
  ]
}
```

For these visible samples, the expected answers are:

```json
{
  "answers": {
    "sample_amber": "iris+kilo",
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
    "sample_amber": "iris+kilo"
  }
}
```

Include every input instance id exactly once.
