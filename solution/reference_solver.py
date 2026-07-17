#!/usr/bin/env python3
import json
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def swept_positions(n, start, stop):
    pos = start
    while True:
        yield pos
        pos = (pos + 1) % n
        if pos == stop:
            return


def apply_subset(instance, chosen):
    bits = [int(ch) for ch in instance["initial"]]
    for key in instance["keys"]:
        if key["name"] not in chosen:
            continue
        for pos in swept_positions(instance["n"], key["start"], key["stop"]):
            bits[pos] ^= 1
    return "".join(str(bit) for bit in bits)


def answer_for(instance):
    names = sorted(key["name"] for key in instance["keys"])
    candidates = []
    for size in range(len(names) + 1):
        for subset in combinations(names, size):
            chosen = set(subset)
            if apply_subset(instance, chosen) == instance["target"]:
                candidates.append("+".join(subset) if subset else "NONE")
    if not candidates:
        raise ValueError(f"no answer for {instance['id']}")
    return min(candidates)


def main():
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: solve.py path/to/instances.json")
    with Path(sys.argv[1]).open() as f:
        instances = json.load(f)["instances"]
    answers = {instance["id"]: answer_for(instance) for instance in instances}
    print(json.dumps({"answers": answers}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
