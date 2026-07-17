#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Optional


DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {name: idx for idx, name in enumerate(DIALS)}

COMMANDS = (
    "move east",
    "move west",
    "push east",
    "take key",
    "turn clockwise",
    "turn counterclockwise",
    "use key",
    "wait",
)


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset[int]
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


def in_bounds(level: Level, pos: int) -> bool:
    return 0 <= pos < level.length


def apply_phases(level: Level, state: State) -> Optional[tuple[State, int]]:
    player = state.player
    crate = state.crate
    wear = 0

    while crate in level.ice:
        crate += 1
        if not in_bounds(level, crate):
            return None
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if state.dial == DIAL_INDEX["E"]:
            dest = crate + 1
            if in_bounds(level, dest) and dest != player:
                crate = dest
        elif state.dial == DIAL_INDEX["W"]:
            dest = crate - 1
            if in_bounds(level, dest) and dest != player:
                crate = dest

    return State(player, crate, state.dial, state.has_key), wear


def can_enter_key_position(level: Level, crate: int, dest: int) -> bool:
    return dest != level.key_position or crate == level.plate


def transition(level: Level, state: State, command: str) -> Optional[tuple[Optional[State], int, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key

    if command == "move east":
        dest = player + 1
        if not in_bounds(level, dest) or dest == crate:
            return None
        if not can_enter_key_position(level, crate, dest):
            return None
        phased = apply_phases(level, State(dest, crate, dial, has_key))
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 0, wear

    if command == "move west":
        dest = player - 1
        if not in_bounds(level, dest) or dest == crate:
            return None
        if not can_enter_key_position(level, crate, dest):
            return None
        phased = apply_phases(level, State(dest, crate, dial, has_key))
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 0, wear

    if command == "push east":
        if player != crate - 1:
            return None
        dest = crate + 1
        if not in_bounds(level, dest):
            return None
        phased = apply_phases(level, State(player, dest, dial, has_key))
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 1, wear

    if command == "take key":
        if has_key or player != level.key_position:
            return None
        phased = apply_phases(level, State(player, crate, dial, True))
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 0, wear

    if command == "turn clockwise":
        phased = apply_phases(level, State(player, crate, (dial + 1) % 4, has_key))
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 0, wear

    if command == "turn counterclockwise":
        phased = apply_phases(level, State(player, crate, (dial - 1) % 4, has_key))
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 0, wear

    if command == "use key":
        if (
            player != level.goal
            or not has_key
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        phased = apply_phases(level, state)
        if phased is None:
            return None
        return None, 0, phased[1]

    if command == "wait":
        phased = apply_phases(level, state)
        if phased is None:
            return None
        next_state, wear = phased
        return next_state, 0, wear

    raise ValueError(f"unknown command: {command}")


def solve(level_data: dict) -> list[str]:
    level = Level(
        length=level_data["length"],
        conveyor=level_data["conveyor"],
        ice=frozenset(level_data["ice"]),
        plate=level_data["plate"],
        key_position=level_data["key_position"],
        goal=level_data["goal"],
        target_dial=DIAL_INDEX[level_data["target_dial"]],
    )
    start = State(
        player=level_data["start"]["player"],
        crate=level_data["start"]["crate"],
        dial=DIAL_INDEX[level_data["start"]["dial"]],
        has_key=bool(level_data["start"]["key"]),
    )

    start_key = (0, 0, 0, ())
    best: dict[State, tuple[int, int, int, tuple[int, ...]]] = {start: start_key}
    heap: list[tuple[int, int, int, tuple[int, ...], Optional[State]]] = [(0, 0, 0, (), start)]

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if state is None:
            return [COMMANDS[idx] for idx in path]
        if best.get(state) != (steps, pushes, wear, path):
            continue

        for idx, command in enumerate(COMMANDS):
            outcome = transition(level, state, command)
            if outcome is None:
                continue
            next_state, push_cost, wear_cost = outcome
            next_key = (
                steps + 1,
                pushes + push_cost,
                wear + wear_cost,
                path + (idx,),
            )
            if next_state is None:
                heapq.heappush(heap, (*next_key, None))
                continue
            if next_key < best.get(next_state, (sys.maxsize, sys.maxsize, sys.maxsize, (sys.maxsize,))):
                best[next_state] = next_key
                heapq.heappush(heap, (*next_key, next_state))

    raise RuntimeError("level is unsolvable")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as handle:
        level_data = json.load(handle)

    commands = solve(level_data)

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))


if __name__ == "__main__":
    main()
