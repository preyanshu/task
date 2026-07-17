#!/usr/bin/env python3
import json
import sys
from itertools import combinations
from pathlib import Path


def beam_mask(instance, beam):
    island_index = {island["name"]: i for i, island in enumerate(instance["islands"])}
    cell_to_island = {}
    for island in instance["islands"]:
        for cell in island["cells"]:
            cell_to_island[tuple(cell)] = island["name"]

    touched = {cell_to_island[tuple(cell)] for cell in beam["cells"]}
    mask = 0
    for name in touched:
        mask ^= 1 << island_index[name]
    return mask


def state_mask(bits):
    mask = 0
    for i, bit in enumerate(bits):
        if bit == "1":
            mask |= 1 << i
    return mask


def answer_for(instance):
    names = sorted(beam["name"] for beam in instance["beams"])
    beams = {beam["name"]: beam for beam in instance["beams"]}
    delta = state_mask(instance["initial"]) ^ state_mask(instance["target"])

    matches = []
    for size in range(len(names) + 1):
        for subset in combinations(names, size):
            mask = 0
            for name in subset:
                mask ^= beam_mask(instance, beams[name])
            if mask == delta:
                matches.append("+".join(subset) if subset else "NONE")
    if not matches:
        raise ValueError(f"no answer for {instance['id']}")
    return min(matches)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: solve.py path/to/instances.json")
    with Path(sys.argv[1]).open() as f:
        instances = json.load(f)["instances"]
    answers = {instance["id"]: answer_for(instance) for instance in instances}
    print(json.dumps({"answers": answers}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
