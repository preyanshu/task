#!/usr/bin/env python3
import json
import sys
from itertools import combinations
from pathlib import Path


DEFAULT_DIAL = "abcdefghijklmnopqrstuvwxyz+"


def dial_key(instance, answer):
    if answer == "NONE":
        return [len(DEFAULT_DIAL) + 1]
    order = {ch: i for i, ch in enumerate(instance.get("dial", DEFAULT_DIAL))}
    return [order[ch] for ch in answer]


def apply_subset(instance, chosen):
    bits = [int(ch) for ch in instance["initial"]]
    cell_to_index = {tuple(island["cell"]): i for i, island in enumerate(instance["islands"])}
    beams = {beam["name"]: beam for beam in instance["beams"]}

    for name in sorted(chosen):
        for cell in beams[name]["path"]:
            index = cell_to_index.get(tuple(cell))
            if index is None:
                continue
            bits[index] ^= 1
            if bits[index] == 0:
                break
    return "".join(str(bit) for bit in bits)


def answer_for(instance):
    names = sorted(beam["name"] for beam in instance["beams"])
    matches = []
    for size in range(len(names) + 1):
        for subset in combinations(names, size):
            if apply_subset(instance, subset) == instance["target"]:
                matches.append("+".join(subset) if subset else "NONE")
    if not matches:
        raise ValueError(f"no answer for {instance['id']}")
    return min(matches, key=lambda answer: dial_key(instance, answer))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: solve.py path/to/instances.json")
    with Path(sys.argv[1]).open() as f:
        instances = json.load(f)["instances"]
    answers = {instance["id"]: answer_for(instance) for instance in instances}
    print(json.dumps({"answers": answers}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
