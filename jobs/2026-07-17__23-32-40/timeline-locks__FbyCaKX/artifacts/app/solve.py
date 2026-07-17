#!/usr/bin/env python3

import heapq
import json
import sys
from dataclasses import dataclass
from typing import Optional


COMMANDS = tuple(
    sorted(
        (
            "move east",
            "move west",
            "push east",
            "take key",
            "turn clockwise",
            "turn counterclockwise",
            "use key",
            "wait",
        )
    )
)
COMMAND_INDEX = {command: index for index, command in enumerate(COMMANDS)}
GOAL_STATE = ("goal",)
DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}


@dataclass(frozen=True, slots=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset[int]
    plate: int
    key_position: int
    goal: int
    target_dial: int


@dataclass(frozen=True, slots=True)
class State:
    player: int
    crate: int
    dial: int
    has_key: bool


def load_level(path: str) -> tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    start = data["start"]
    level = Level(
        length=data["length"],
        conveyor=data["conveyor"],
        ice=frozenset(data["ice"]),
        plate=data["plate"],
        key_position=data["key_position"],
        goal=data["goal"],
        target_dial=DIAL_INDEX[data["target_dial"]],
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


def can_enter(level: Level, state: State, destination: int) -> bool:
    if destination < 0 or destination >= level.length:
        return False
    if destination == state.crate:
        return False
    if destination == level.key_position and not route_open(level, state):
        return False
    return True


def rotate(dial: int, step: int) -> int:
    return (dial + step) % len(DIALS)


def post_command(level: Level, state: State) -> tuple[State, int]:
    crate = state.crate
    wear = 0

    while crate in level.ice:
        next_crate = crate + 1
        if next_crate >= level.length or next_crate == state.player:
            break
        crate = next_crate
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        direction = 0
        if state.dial == DIAL_INDEX["E"]:
            direction = 1
        elif state.dial == DIAL_INDEX["W"]:
            direction = -1
        if direction:
            destination = crate + direction
            if 0 <= destination < level.length and destination != state.player:
                crate = destination

    return State(state.player, crate, state.dial, state.has_key), wear


def apply_command(level: Level, state: State, command: str):
    if command == "move east":
        destination = state.player + 1
        if not can_enter(level, state, destination):
            return None
        next_state = State(destination, state.crate, state.dial, state.has_key)
        next_state, wear = post_command(level, next_state)
        return next_state, 0, wear

    if command == "move west":
        destination = state.player - 1
        if not can_enter(level, state, destination):
            return None
        next_state = State(destination, state.crate, state.dial, state.has_key)
        next_state, wear = post_command(level, next_state)
        return next_state, 0, wear

    if command == "push east":
        if state.player != state.crate - 1:
            return None
        destination = state.crate + 1
        if destination >= level.length:
            return None
        next_state = State(state.player, destination, state.dial, state.has_key)
        next_state, wear = post_command(level, next_state)
        return next_state, 1, wear

    if command == "take key":
        if state.player != level.key_position or state.has_key:
            return None
        next_state = State(state.player, state.crate, state.dial, True)
        next_state, wear = post_command(level, next_state)
        return next_state, 0, wear

    if command == "turn clockwise":
        next_state = State(state.player, state.crate, rotate(state.dial, 1), state.has_key)
        next_state, wear = post_command(level, next_state)
        return next_state, 0, wear

    if command == "turn counterclockwise":
        next_state = State(state.player, state.crate, rotate(state.dial, -1), state.has_key)
        next_state, wear = post_command(level, next_state)
        return next_state, 0, wear

    if command == "use key":
        if (
            state.player == level.goal
            and state.has_key
            and state.crate == level.plate
            and state.dial == level.target_dial
        ):
            _, wear = post_command(level, state)
            return GOAL_STATE, 0, wear
        return None

    if command == "wait":
        next_state, wear = post_command(level, state)
        return next_state, 0, wear

    raise ValueError(f"unknown command: {command}")


def solve(level: Level, start: State) -> list[str]:
    start_cost = (0, 0, 0, ())
    best = {start: start_cost}
    heap = [(0, 0, 0, (), start)]

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if best.get(state) != (steps, pushes, wear, path):
            continue
        if state == GOAL_STATE:
            return [COMMANDS[index] for index in path]

        for command in COMMANDS:
            transition = apply_command(level, state, command)
            if transition is None:
                continue
            next_state, extra_pushes, extra_wear = transition
            next_path = path + (COMMAND_INDEX[command],)
            candidate = (steps + 1, pushes + extra_pushes, wear + extra_wear, next_path)
            previous = best.get(next_state)
            if previous is None or candidate < previous:
                best[next_state] = candidate
                heapq.heappush(heap, (*candidate, next_state))

    raise RuntimeError("level is unsolvable")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
