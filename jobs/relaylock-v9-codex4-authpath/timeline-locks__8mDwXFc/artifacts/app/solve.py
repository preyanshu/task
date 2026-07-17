#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


COMMANDS = [
    "move east",
    "move west",
    "push east",
    "take key",
    "turn clockwise",
    "turn counterclockwise",
    "use key",
    "wait",
]
COMMANDS.sort()

DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: int
    has_key: bool


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: int


def parse_level(path: str) -> Tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    start = raw["start"]
    level = Level(
        length=raw["length"],
        conveyor=raw["conveyor"],
        ice=frozenset(raw["ice"]),
        plate=raw["plate"],
        key_position=raw["key_position"],
        goal=raw["goal"],
        target_dial=DIAL_TO_INDEX[raw["target_dial"]],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIAL_TO_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def key_route_open(level: Level, crate_position: int) -> bool:
    return crate_position == level.plate


def can_player_enter(level: Level, state: State, position: int) -> bool:
    if not in_bounds(level, position):
        return False
    if position == state.crate:
        return False
    if position == level.key_position and not key_route_open(level, state.crate):
        return False
    return True


def apply_sliding(level: Level, player: int, crate: int) -> Tuple[int, int]:
    wear = 0
    while crate in level.ice:
        next_crate = crate + 1
        if not in_bounds(level, next_crate):
            break
        if next_crate == player:
            break
        crate = next_crate
        if crate in level.ice:
            wear += 1
    return crate, wear


def apply_conveyor(level: Level, player: int, crate: int, dial: int) -> int:
    if level.conveyor is None or crate != level.conveyor:
        return crate
    if dial == DIAL_TO_INDEX["E"]:
        destination = crate + 1
    elif dial == DIAL_TO_INDEX["W"]:
        destination = crate - 1
    else:
        return crate
    if not in_bounds(level, destination):
        return crate
    if destination == player:
        return crate
    return destination


def transition(level: Level, state: State, command: str) -> Optional[Tuple[Optional[State], int, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    pushes = 0

    if command == "move east":
        destination = player + 1
        if not can_player_enter(level, state, destination):
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if not can_player_enter(level, state, destination):
            return None
        player = destination
    elif command == "push east":
        if player != crate - 1:
            return None
        destination = crate + 1
        if not in_bounds(level, destination):
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
        return None, 0, 0
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    crate, wear = apply_sliding(level, player, crate)
    crate = apply_conveyor(level, player, crate, dial)
    next_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
    return next_state, pushes, wear


def solve(level: Level, start: State) -> List[str]:
    start_key = (0, 0, 0, ())
    heap: List[Tuple[int, int, int, Tuple[int, ...], State]] = [
        (0, 0, 0, (), start)
    ]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_key}

    while heap:
        steps, pushes, wear, path_codes, state = heapq.heappop(heap)
        current_key = (steps, pushes, wear, path_codes)
        if best.get(state) != current_key:
            continue

        for command_index, command in enumerate(COMMANDS):
            result = transition(level, state, command)
            if result is None:
                continue

            next_steps = steps + 1
            next_pushes = pushes + (1 if command == "push east" else 0)
            next_path = path_codes + (command_index,)

            if result[0] is None:
                return [COMMANDS[index] for index in next_path]

            next_state, _, added_wear = result
            next_wear = wear + added_wear
            next_key = (next_steps, next_pushes, next_wear, next_path)

            previous = best.get(next_state)
            if previous is not None and previous <= next_key:
                continue
            best[next_state] = next_key
            heapq.heappush(
                heap,
                (next_steps, next_pushes, next_wear, next_path, next_state),
            )

    raise RuntimeError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("Usage: python3 /app/solve.py <level.json> <output.json>")

    level, start = parse_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
