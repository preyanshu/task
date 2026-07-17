#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: int


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: int
    has_key: bool


def load_level(path: str) -> Tuple[Level, State]:
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
        target_dial=DIAL_INDEX[raw["target_dial"]],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIAL_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def route_open(level: Level, state: State) -> bool:
    return state.crate == level.plate


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def apply_post_phases(level: Level, state: State) -> Optional[Tuple[State, int]]:
    crate = state.crate
    wear = 0

    while crate in level.ice:
        destination = crate + 1
        if not in_bounds(level, destination):
            return None
        crate = destination
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if state.dial == DIAL_INDEX["E"]:
            destination = crate + 1
            if in_bounds(level, destination) and destination != state.player:
                crate = destination
        elif state.dial == DIAL_INDEX["W"]:
            destination = crate - 1
            if in_bounds(level, destination) and destination != state.player:
                crate = destination

    return State(state.player, crate, state.dial, state.has_key), wear


def step(level: Level, state: State, command: str) -> Optional[Tuple[Optional[State], int, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    push_cost = 0

    if command == "move east":
        destination = player + 1
        if not in_bounds(level, destination):
            return None
        if destination == crate:
            return None
        if destination == level.key_position and not route_open(level, state):
            return None
        next_state = State(destination, crate, dial, has_key)
    elif command == "move west":
        destination = player - 1
        if not in_bounds(level, destination):
            return None
        if destination == crate:
            return None
        if destination == level.key_position and not route_open(level, state):
            return None
        next_state = State(destination, crate, dial, has_key)
    elif command == "turn clockwise":
        next_state = State(player, crate, (dial + 1) % 4, has_key)
    elif command == "turn counterclockwise":
        next_state = State(player, crate, (dial - 1) % 4, has_key)
    elif command == "push east":
        if player != crate - 1:
            return None
        destination = crate + 1
        if not in_bounds(level, destination):
            return None
        push_cost = 1
        next_state = State(player, destination, dial, has_key)
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        next_state = State(player, crate, dial, True)
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
        next_state = state
    else:
        return None

    post_result = apply_post_phases(level, next_state)
    if post_result is None:
        return None
    post_state, wear = post_result
    return post_state, push_cost, wear


def solve(level: Level, start: State) -> List[str]:
    start_key = (0, 0, 0, ())
    heap: List[Tuple[int, int, int, Tuple[int, ...], State]] = [(0, 0, 0, (), start)]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_key}

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        key = (steps, pushes, wear, path)
        if best.get(state) != key:
            continue

        for command_index, command in enumerate(COMMANDS):
            result = step(level, state, command)
            if result is None:
                continue

            next_state, push_cost, wear_cost = result
            next_key = (
                steps + 1,
                pushes + push_cost,
                wear + wear_cost,
                path + (command_index,),
            )

            if next_state is None:
                return [COMMANDS[index] for index in next_key[3]]

            previous = best.get(next_state)
            if previous is None or next_key < previous:
                best[next_state] = next_key
                heapq.heappush(heap, (next_key[0], next_key[1], next_key[2], next_key[3], next_state))

    raise RuntimeError("level is unsolvable")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
