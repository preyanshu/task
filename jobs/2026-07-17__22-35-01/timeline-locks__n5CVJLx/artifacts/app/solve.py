#!/usr/bin/env python3

import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Union


COMMANDS = tuple(
    sorted(
        (
            "move east",
            "move west",
            "turn clockwise",
            "turn counterclockwise",
            "push east",
            "take key",
            "use key",
            "wait",
        )
    )
)

DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}
TERMINAL = ("SOLVED",)
Cost = Tuple[int, int, int, Tuple[str, ...]]
State = Tuple[int, int, int, bool]
Key = Union[State, Tuple[str]]


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: int
    start: State


def load_level(path: str) -> Level:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    start = raw["start"]
    target_dial = raw["target_dial"]
    return Level(
        length=raw["length"],
        conveyor=raw["conveyor"],
        ice=frozenset(raw["ice"]),
        plate=raw["plate"],
        key_position=raw["key_position"],
        goal=raw["goal"],
        target_dial=DIAL_INDEX[target_dial],
        start=(
            start["player"],
            start["crate"],
            DIAL_INDEX[start["dial"]],
            bool(start["key"]),
        ),
    )


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def apply_command(
    level: Level, state: State, command: str
) -> Optional[Tuple[Key, int, int]]:
    player, crate, dial, has_key = state
    pushes = 0
    wear = 0
    solved = False

    route_open = crate == level.plate

    if command == "move east":
        destination = player + 1
        if not in_bounds(level, destination) or destination == crate:
            return None
        if destination == level.key_position and not route_open:
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if not in_bounds(level, destination) or destination == crate:
            return None
        if destination == level.key_position and not route_open:
            return None
        player = destination
    elif command == "push east":
        destination = crate + 1
        if player != crate - 1 or not in_bounds(level, destination):
            return None
        crate = destination
        pushes = 1
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        has_key = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "use key":
        if (
            player != level.goal
            or not has_key
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        solved = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    while crate in level.ice:
        destination = crate + 1
        if not in_bounds(level, destination) or destination == player:
            return None
        crate = destination
        wear += 1

    if level.conveyor is not None and crate == level.conveyor and DIALS[dial] in ("E", "W"):
        delta = 1 if DIALS[dial] == "E" else -1
        destination = crate + delta
        if in_bounds(level, destination) and destination != player:
            crate = destination

    if solved:
        return TERMINAL, pushes, wear
    return (player, crate, dial, has_key), pushes, wear


def solve(level: Level) -> List[str]:
    start_state = level.start
    start_cost: Cost = (0, 0, 0, ())
    heap: List[Tuple[int, int, int, Tuple[str, ...], Key]] = [
        (*start_cost, start_state)
    ]
    best: Dict[Key, Cost] = {start_state: start_cost}

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        current_cost = (steps, pushes, wear, path)
        if best.get(state) != current_cost:
            continue
        if state == TERMINAL:
            return list(path)

        current_state = state
        for command in COMMANDS:
            result = apply_command(level, current_state, command)
            if result is None:
                continue
            next_state, push_inc, wear_inc = result
            next_cost: Cost = (
                steps + 1,
                pushes + push_inc,
                wear + wear_inc,
                path + (command,),
            )
            previous = best.get(next_state)
            if previous is None or next_cost < previous:
                best[next_state] = next_cost
                heapq.heappush(heap, (*next_cost, next_state))

    raise RuntimeError("level is unsolvable")


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level = load_level(args[1])
    commands = solve(level)

    with open(args[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
