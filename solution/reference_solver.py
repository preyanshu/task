#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def final_state(instance):
    n = instance["n"]
    bits = [int(ch) for ch in instance["initial"]]
    tokens = [token.copy() for token in instance["tokens"]]

    for tick in range(instance["ticks"]):
        proposals = []
        for token in tokens:
            move = token["moves"][tick % len(token["moves"])]
            dest = token["pos"]
            if move == "L":
                dest = (dest - 1) % n
            elif move == "R":
                dest = (dest + 1) % n
            elif move != "S":
                raise ValueError(f"bad move {move!r}")
            proposals.append(dest)

        counts = {dest: proposals.count(dest) for dest in set(proposals)}
        for token, dest in zip(tokens, proposals):
            if counts[dest] >= 2:
                bits[token["pos"]] ^= 1
            else:
                token["pos"] = dest
                bits[dest] ^= 1

    return "".join(str(bit) for bit in bits)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: solve.py path/to/instances.json")
    with Path(sys.argv[1]).open() as f:
        instances = json.load(f)["instances"]
    answers = {instance["id"]: final_state(instance) for instance in instances}
    print(json.dumps({"answers": answers}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
