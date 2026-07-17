You are solving Timeline Locks.

Write a solver at `solution/solve.py`.

Each instance describes a small grid of named islands and named beams. Every island has
one or more grid cells and one binary lock bit. The island order in the input is also the
order of bits in `initial` and `target`.

You may activate any subset of beams at most once. When a beam is activated, look at the
set of islands that contain at least one cell listed by that beam. Each island in that
set flips its lock bit exactly once for that beam.

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
      "target": "11111",
      "islands": [
        {"name": "A", "cells": [[0, 0]]},
        {"name": "B", "cells": [[0, 2]]},
        {"name": "C", "cells": [[1, 1]]},
        {"name": "D", "cells": [[2, 0]]},
        {"name": "E", "cells": [[2, 2]]}
      ],
      "beams": [
        {"name": "iris", "cells": [[0, 0], [1, 1]]},
        {"name": "jade", "cells": [[0, 2], [2, 2]]},
        {"name": "kilo", "cells": [[2, 0]]},
        {"name": "lumen", "cells": [[0, 0], [2, 2]]},
        {"name": "moss", "cells": [[1, 1], [2, 0]]}
      ]
    },
    {
      "id": "sample_brass",
      "initial": "101100",
      "target": "001001",
      "islands": [
        {"name": "A", "cells": [[0, 1]]},
        {"name": "B", "cells": [[1, 0]]},
        {"name": "C", "cells": [[1, 2]]},
        {"name": "D", "cells": [[2, 1]]},
        {"name": "E", "cells": [[3, 0]]},
        {"name": "F", "cells": [[3, 2]]}
      ],
      "beams": [
        {"name": "ash", "cells": [[0, 1], [1, 0]]},
        {"name": "bryn", "cells": [[1, 2], [2, 1]]},
        {"name": "cove", "cells": [[3, 0], [3, 2]]},
        {"name": "dune", "cells": [[0, 1], [3, 2]]},
        {"name": "elm", "cells": [[1, 0], [2, 1], [3, 0]]}
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
