#!/usr/bin/env python3
import json
import heapq
import sys
from typing import List, Tuple


COMMANDS = sorted(
    [
        "move east",
        "move west",
        "turn clockwise",
        "turn counterclockwise",
        "push east",
        "take key",
        "use key",
        "wait",
    ]
)

DIAL_TO_INT = {"N": 0, "E": 1, "S": 2, "W": 3}

# State tuple:
# (player_position, crate_position, dial, has_key, crate_momentum)
# crate_momentum is -1, 0, or 1.
SOLVED = (-1,)


def load_level(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def slide_crate(
    player: int,
    crate: int,
    momentum: int,
    length: int,
    ice: set,
) -> Tuple[int, int]:
    wear = 0
    if momentum == 0:
        return crate, wear

    while crate in ice:
        nxt = crate + momentum
        if nxt < 0 or nxt >= length or nxt == player:
            break
        crate = nxt
        if crate in ice:
            wear += 1
    return crate, wear


def apply_command(state: Tuple[int, int, int, bool, int], command: str, level: dict):
    player, crate, dial, has_key, momentum = state
    length = level["length"]
    key_position = level["key_position"]
    plate = level["plate"]
    goal = level["goal"]
    conveyor = level["conveyor"]
    target_dial = DIAL_TO_INT[level["target_dial"]]
    ice = level["_ice_set"]

    pushes = 0
    wear = 0
    attempted_unlock = False

    if command == "move east":
        nxt = player + 1
        if nxt >= length or nxt == crate:
            return None
        if nxt == key_position and crate != plate:
            return None
        player = nxt
    elif command == "move west":
        nxt = player - 1
        if nxt < 0 or nxt == crate:
            return None
        if nxt == key_position and crate != plate:
            return None
        player = nxt
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player + 1 != crate:
            return None
        nxt = crate + 1
        if nxt >= length:
            return None
        crate = nxt
        momentum = 1
        pushes = 1
    elif command == "take key":
        if player != key_position or has_key:
            return None
        has_key = True
    elif command == "use key":
        if not (player == goal and has_key and crate == plate and dial == target_dial):
            return None
        attempted_unlock = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate, slide_wear = slide_crate(player, crate, momentum, length, ice)
    wear += slide_wear

    if conveyor is not None and crate == conveyor and dial in (1, 3):
        step = 1 if dial == 1 else -1
        nxt = crate + step
        if 0 <= nxt < length and nxt != player:
            crate = nxt
            momentum = step

    solved = attempted_unlock and crate == plate
    next_state = (player, crate, dial, has_key, momentum)
    return next_state, pushes, wear, solved


def solve(level: dict):
    initial = level["start"]
    start_state = (
        initial["player"],
        initial["crate"],
        DIAL_TO_INT[initial["dial"]],
        bool(initial["key"]),
        0,
    )

    heap = [(0, 0, 0, tuple(), start_state)]
    best = {start_state: (0, 0, 0, tuple())}

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        current_cost = (steps, pushes, wear, path)
        if best.get(state) != current_cost:
            continue
        if state == SOLVED:
            return list(path)

        for command in COMMANDS:
            result = apply_command(state, command, level)
            if result is None:
                continue

            next_state, push_delta, wear_delta, solved = result
            new_path = path + (command,)
            new_cost = (steps + 1, pushes + push_delta, wear + wear_delta, new_path)
            candidate_state = SOLVED if solved else next_state
            if new_cost < best.get(candidate_state, (float("inf"),) * 4):
                best[candidate_state] = new_cost
                heapq.heappush(
                    heap,
                    (new_cost[0], new_cost[1], new_cost[2], new_cost[3], candidate_state),
                )

    raise RuntimeError("level has no solution")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level = load_level(argv[1])
    level["_ice_set"] = set(level["ice"])
    commands = solve(level)

    output = json.dumps({"commands": commands}, separators=(",", ":"))
    with open(argv[2], "w", encoding="utf-8") as handle:
        handle.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
