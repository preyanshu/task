#!/usr/bin/env python3

import json
import sys
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
CLOCKWISE = {"N": "E", "E": "S", "S": "W", "W": "N"}
COUNTERCLOCKWISE = {"N": "W", "W": "S", "S": "E", "E": "N"}
CONVEYOR_DELTA = {"N": 0, "E": 1, "S": 0, "W": -1}
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
COMMAND_INDEX = {command: index for index, command in enumerate(COMMANDS)}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: str


Cost = Tuple[int, int, Tuple[int, ...]]
BestEntry = Tuple[int, int, Tuple[int, ...]]


def parse_level(path: str) -> Tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    start = raw["start"]
    level = Level(
        length=raw["length"],
        conveyor=raw.get("conveyor"),
        ice=frozenset(raw["ice"]),
        plate=raw["plate"],
        key_position=raw["key_position"],
        goal=raw["goal"],
        target_dial=raw["target_dial"],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=start["dial"],
        has_key=bool(start["key"]),
    )
    return level, state


def crate_on_plate(level: Level, state: State) -> bool:
    return state.crate == level.plate


def can_enter(level: Level, state: State, position: int) -> bool:
    return 0 <= position < level.length and position != state.crate


def move_crate(level: Level, player: int, crate: int, delta: int) -> Optional[int]:
    target = crate + delta
    if not (0 <= target < level.length):
        return None
    if target == player:
        return None
    return target


def apply_primary(level: Level, state: State, command: str) -> Optional[Tuple[State, bool, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    solved = False
    wear = 0

    if command == "move east":
        target = player + 1
        if not can_enter(level, state, target):
            return None
        player = target
    elif command == "move west":
        target = player - 1
        if not can_enter(level, state, target):
            return None
        player = target
    elif command == "push east":
        if player + 1 != crate:
            return None
        target = move_crate(level, player, crate, 1)
        if target is None:
            return None
        crate = target
        if crate in level.ice:
            wear += 1
    elif command == "turn clockwise":
        dial = CLOCKWISE[dial]
    elif command == "turn counterclockwise":
        dial = COUNTERCLOCKWISE[dial]
    elif command == "take key":
        if has_key:
            return None
        if player != level.key_position:
            return None
        if crate != level.plate:
            return None
        has_key = True
    elif command == "use key":
        if player != level.goal:
            return None
        if not has_key:
            return None
        if crate != level.plate:
            return None
        if dial != level.target_dial:
            return None
        solved = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    return State(player=player, crate=crate, dial=dial, has_key=has_key), solved, wear


def apply_ice(level: Level, state: State) -> Tuple[State, int]:
    crate = state.crate
    wear = 0

    while crate in level.ice:
        target = move_crate(level, state.player, crate, 1)
        if target is None:
            break
        crate = target
        if crate in level.ice:
            wear += 1

    return State(player=state.player, crate=crate, dial=state.dial, has_key=state.has_key), wear


def apply_conveyor(level: Level, state: State) -> Tuple[State, int]:
    if level.conveyor is None or state.crate != level.conveyor:
        return state, 0

    delta = CONVEYOR_DELTA[state.dial]
    if delta == 0:
        return state, 0

    target = move_crate(level, state.player, state.crate, delta)
    if target is None:
        return state, 0

    wear = 1 if target in level.ice else 0
    return (
        State(player=state.player, crate=target, dial=state.dial, has_key=state.has_key),
        wear,
    )


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, bool]]:
    primary = apply_primary(level, state, command)
    if primary is None:
        return None

    next_state, solved, wear = primary
    next_state, added_wear = apply_ice(level, next_state)
    wear += added_wear
    next_state, added_wear = apply_conveyor(level, next_state)
    wear += added_wear
    return next_state, wear, solved


def better_cost(candidate: Cost, current: Cost) -> bool:
    return candidate < current


def solve(level: Level, start: State) -> List[str]:
    initial_key: Tuple[int, int, Tuple[int, ...]] = (0, 0, ())
    frontier: Deque[State] = deque([start])
    best: Dict[State, BestEntry] = {start: initial_key}

    while frontier:
        state = frontier.popleft()
        pushes, wear, path = best[state]
        depth = len(path)

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, added_wear, solved = result
            next_path = path + (COMMAND_INDEX[command],)
            next_cost: Cost = (
                pushes + (1 if command == "push east" else 0),
                wear + added_wear,
                next_path,
            )

            if solved:
                return [COMMANDS[index] for index in next_path]

            if next_state in best and not better_cost(next_cost, best[next_state]):
                continue

            best[next_state] = next_cost
            frontier.append(next_state)

    raise RuntimeError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level, start = parse_level(argv[1])
    commands = solve(level, start)
    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
