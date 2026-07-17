#!/usr/bin/env python3

from __future__ import annotations

import heapq
import json
import sys
from dataclasses import dataclass
from typing import Optional


DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}
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


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: int
    has_key: bool
    crate_dir: int


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset[int]
    plate: int
    key_position: int
    goal: int
    target_dial: int


def conveyor_delta(dial_index: int) -> int:
    dial = DIALS[dial_index]
    if dial == "E":
        return 1
    if dial == "W":
        return -1
    return 0


def enter_ice_wear(position: int, ice: frozenset[int]) -> int:
    return 1 if position in ice else 0


def transition(level: Level, state: State, command: str) -> Optional[tuple[State, int, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    crate_dir = state.crate_dir
    pushes = 0
    wear = 0
    used_key = False

    if command == "move east":
        next_player = player + 1
        if next_player >= level.length or next_player == crate:
            return None
        player = next_player
    elif command == "move west":
        next_player = player - 1
        if next_player < 0 or next_player == crate:
            return None
        player = next_player
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player != crate - 1:
            return None
        next_crate = crate + 1
        if next_crate >= level.length:
            return None
        crate = next_crate
        crate_dir = 1
        pushes = 1
        wear += enter_ice_wear(crate, level.ice)
    elif command == "take key":
        if has_key or player != level.key_position or crate != level.plate:
            return None
        has_key = True
    elif command == "use key":
        if (
            not has_key
            or player != level.goal
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    if crate_dir != 0:
        while crate in level.ice:
            next_crate = crate + crate_dir
            if next_crate < 0 or next_crate >= level.length or next_crate == player:
                break
            crate = next_crate
            wear += enter_ice_wear(crate, level.ice)

    if level.conveyor is not None and crate == level.conveyor:
        delta = conveyor_delta(dial)
        next_crate = crate + delta
        if delta != 0 and 0 <= next_crate < level.length and next_crate != player:
            crate = next_crate
            crate_dir = delta
            wear += enter_ice_wear(crate, level.ice)

    solved = False
    if used_key and crate == level.plate and dial == level.target_dial and player == level.goal:
        solved = True

    return State(player, crate, dial, has_key, crate_dir), pushes, wear, solved


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
        crate_dir=0,
    )

    start_key = (0, 0, 0, ())
    best_for_state = {start: start_key}
    queue = [(0, 0, 0, (), start)]
    best_solution = None

    while queue:
        steps, pushes, wear, commands, state = heapq.heappop(queue)
        current_key = (steps, pushes, wear, commands)
        if best_for_state.get(state) != current_key:
            continue
        if best_solution is not None and current_key >= best_solution:
            break

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, push_delta, wear_delta, solved = result
            next_commands = commands + (command,)
            next_key = (
                steps + 1,
                pushes + push_delta,
                wear + wear_delta,
                next_commands,
            )

            if solved:
                if best_solution is None or next_key < best_solution:
                    best_solution = next_key
                continue

            previous = best_for_state.get(next_state)
            if previous is None or next_key < previous:
                best_for_state[next_state] = next_key
                heapq.heappush(
                    queue,
                    (next_key[0], next_key[1], next_key[2], next_key[3], next_state),
                )

    if best_solution is None:
        raise RuntimeError("no solution found")

    return list(best_solution[3])


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    with open(sys.argv[1], "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = solve(level_data)

    with open(sys.argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main()
