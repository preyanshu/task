#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}

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
COMMAND_TO_INDEX = {command: index for index, command in enumerate(COMMANDS)}


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


def load_level(path: str) -> Tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    start = raw["start"]
    level = Level(
        length=int(raw["length"]),
        conveyor=raw["conveyor"],
        ice=frozenset(int(cell) for cell in raw["ice"]),
        plate=int(raw["plate"]),
        key_position=int(raw["key_position"]),
        goal=int(raw["goal"]),
        target_dial=DIAL_TO_INDEX[raw["target_dial"]],
    )
    state = State(
        player=int(start["player"]),
        crate=int(start["crate"]),
        dial=DIAL_TO_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def rotate_clockwise(dial: int) -> int:
    return (dial + 1) % len(DIALS)


def rotate_counterclockwise(dial: int) -> int:
    return (dial - 1) % len(DIALS)


def can_take_key(level: Level, state: State) -> bool:
    return (
        state.player == level.key_position
        and not state.has_key
        and state.crate == level.plate
    )


def can_use_key(level: Level, state: State) -> bool:
    return (
        state.player == level.goal
        and state.has_key
        and state.crate == level.plate
        and state.dial == level.target_dial
    )


def move_crate(
    level: Level,
    player: int,
    crate: int,
    delta: int,
    wear: int,
) -> Tuple[int, int]:
    destination = crate + delta
    if not (0 <= destination < level.length):
        return crate, wear
    if destination == player:
        return crate, wear
    crate = destination
    if crate in level.ice:
        wear += 1
    return crate, wear


def apply_command(level: Level, state: State, command: str) -> Optional[Tuple[State, bool, int, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    attempted_take = False
    attempted_use = False
    pushes = 0
    wear = 0

    if command == "move east":
        destination = player + 1
        if destination >= level.length or destination == crate:
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if destination < 0 or destination == crate:
            return None
        player = destination
    elif command == "push east":
        if player != crate - 1 or crate + 1 >= level.length:
            return None
        crate, wear = move_crate(level, player, crate, 1, wear)
        if crate == state.crate:
            return None
        pushes = 1
    elif command == "turn clockwise":
        dial = rotate_clockwise(dial)
    elif command == "turn counterclockwise":
        dial = rotate_counterclockwise(dial)
    elif command == "take key":
        if state.player != level.key_position or state.has_key:
            return None
        attempted_take = True
    elif command == "use key":
        if not can_use_key(level, state):
            return None
        attempted_use = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    while crate in level.ice:
        next_crate, wear = move_crate(level, player, crate, 1, wear)
        if next_crate == crate:
            break
        crate = next_crate

    if level.conveyor is not None and crate == level.conveyor:
        delta = 0
        if dial == DIAL_TO_INDEX["E"]:
            delta = 1
        elif dial == DIAL_TO_INDEX["W"]:
            delta = -1
        if delta:
            crate, wear = move_crate(level, player, crate, delta, wear)

    next_state = State(player, crate, dial, has_key)
    if attempted_take and can_take_key(level, next_state):
        next_state = State(player, crate, dial, True)
    solved = attempted_use and can_use_key(level, next_state)
    return next_state, solved, pushes, wear


def solve(level: Level, start: State) -> List[str]:
    frontier: List[Tuple[int, int, int, Tuple[int, ...], State]] = []
    heapq.heappush(frontier, (0, 0, 0, (), start))
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {
        start: (0, 0, 0, ())
    }

    while frontier:
        steps, pushes, wear, path, state = heapq.heappop(frontier)
        if best.get(state) != (steps, pushes, wear, path):
            continue

        for command in COMMANDS:
            result = apply_command(level, state, command)
            if result is None:
                continue

            next_state, solved, extra_pushes, extra_wear = result
            command_index = COMMAND_TO_INDEX[command]
            next_cost = (
                steps + 1,
                pushes + extra_pushes,
                wear + extra_wear,
                path + (command_index,),
            )

            if solved:
                return [COMMANDS[index] for index in next_cost[3]]

            current_best = best.get(next_state)
            if current_best is None or next_cost < current_best:
                best[next_state] = next_cost
                heapq.heappush(frontier, (*next_cost, next_state))

    raise RuntimeError("no solution found")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)
    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, ensure_ascii=True, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
