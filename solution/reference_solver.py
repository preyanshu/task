#!/usr/bin/env python3
import json
import sys
from itertools import combinations
from pathlib import Path


def route_mask(instance, route):
    lock_index = {lock["name"]: i for i, lock in enumerate(instance["locks"])}
    n = len(instance["locks"])
    start = lock_index[route["from"]]
    stop = lock_index[route["to"]]
    mask = 1 << start
    pos = start
    while True:
        pos = (pos + 1) % n
        mask ^= 1 << pos
        if pos == stop:
            return mask


def state_mask(bits):
    mask = 0
    for i, bit in enumerate(bits):
        if bit == "1":
            mask |= 1 << i
    return mask


def apply_subset(instance, chosen):
    mask = state_mask(instance["initial"])
    routes = {route["name"]: route for route in instance["routes"]}
    for name in sorted(chosen):
        mask ^= route_mask(instance, routes[name])
    return "".join("1" if mask >> i & 1 else "0" for i in range(len(instance["locks"])))


def answer_for(instance):
    names = sorted(route["name"] for route in instance["routes"])
    matches = []
    for size in range(len(names) + 1):
        for subset in combinations(names, size):
            if apply_subset(instance, subset) == instance["target"]:
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
