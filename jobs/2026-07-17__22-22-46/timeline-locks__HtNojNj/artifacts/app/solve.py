#!/usr/bin/env python3

import heapq
import json
import sys
from typing import Dict, List, Optional, Tuple


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

DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}

State = Tuple[int, int, int, bool]
Cost = Tuple[int, int, int, Tuple[str, ...]]


class Level:
    def __init__(self, payload: Dict[str, object]) -> None:
        self.length = int(payload["length"])
        start = payload["start"]
        if not isinstance(start, dict):
            raise ValueError("start must be an object")
        self.start_player = int(start["player"])
        self.start_crate = int(start["crate"])
        self.start_dial = DIAL_INDEX[str(start["dial"])]
        self.start_key = bool(start["key"])
        conveyor = payload["conveyor"]
        self.conveyor = None if conveyor is None else int(conveyor)
        self.ice = frozenset(int(value) for value in payload["ice"])
        self.plate = int(payload["plate"])
        self.key_position = int(payload["key_position"])
        self.goal = int(payload["goal"])
        self.target_dial = DIAL_INDEX[str(payload["target_dial"])]

    @property
    def start_state(self) -> State:
        return (
            self.start_player,
            self.start_crate,
            self.start_dial,
            self.start_key,
        )


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def key_route_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def apply_command(level: Level, state: State, command: str) -> Optional[Tuple[Optional[State], int, int]]:
    player, crate, dial, has_key = state
    pushes = 0
    wear = 0

    if command == "move east":
        target = player + 1
        if not in_bounds(level, target) or target == crate:
            return None
        if target == level.key_position and not key_route_open(level, crate):
            return None
        player = target
    elif command == "move west":
        target = player - 1
        if not in_bounds(level, target) or target == crate:
            return None
        if target == level.key_position and not key_route_open(level, crate):
            return None
        player = target
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        target = crate + 1
        if player != crate - 1 or not in_bounds(level, target) or target == player:
            return None
        crate = target
        pushes = 1
    elif command == "take key":
        if player != level.key_position or has_key:
            return None
        has_key = True
    elif command == "use key":
        if (
            player != level.goal
            or not has_key
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        return None, 0, 0
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    while crate in level.ice:
        next_crate = crate + 1
        if not in_bounds(level, next_crate) or next_crate == player:
            return None
        crate = next_crate
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if dial == DIAL_INDEX["E"]:
            next_crate = crate + 1
            if in_bounds(level, next_crate) and next_crate != player:
                crate = next_crate
        elif dial == DIAL_INDEX["W"]:
            next_crate = crate - 1
            if in_bounds(level, next_crate) and next_crate != player:
                crate = next_crate

    return (player, crate, dial, has_key), pushes, wear


def solve(level: Level) -> List[str]:
    start = level.start_state
    start_cost: Cost = (0, 0, 0, ())
    best: Dict[State, Cost] = {start: start_cost}
    heap: List[Tuple[int, int, int, Tuple[str, ...], Optional[State]]] = [
        (0, 0, 0, (), start)
    ]

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if state is None:
            return list(path)
        cost = (steps, pushes, wear, path)
        if best.get(state) != cost:
            continue

        for command in COMMANDS:
            transition = apply_command(level, state, command)
            if transition is None:
                continue
            next_state, extra_pushes, extra_wear = transition
            next_path = path + (command,)
            entry = (
                steps + 1,
                pushes + extra_pushes,
                wear + extra_wear,
                next_path,
                next_state,
            )
            if next_state is None:
                heapq.heappush(heap, entry)
                continue
            next_cost = entry[:4]
            if next_state not in best or next_cost < best[next_state]:
                best[next_state] = next_cost
                heapq.heappush(heap, entry)

    raise RuntimeError("level is unsolvable")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    level = Level(payload)
    commands = solve(level)

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))


if __name__ == "__main__":
    main()
