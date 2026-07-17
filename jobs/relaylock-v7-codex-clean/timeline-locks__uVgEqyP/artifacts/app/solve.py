#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
COMMANDS = sorted(
    [
        "move east",
        "move west",
        "push east",
        "take key",
        "turn clockwise",
        "turn counterclockwise",
        "use key",
        "wait",
    ]
)
COMMAND_INDEX = {command: index for index, command in enumerate(COMMANDS)}


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
        target_dial=DIALS.index(raw["target_dial"]),
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIALS.index(start["dial"]),
        has_key=bool(start["key"]),
    )
    return level, state


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def can_cross_plate(state: State, level: Level, step: int) -> bool:
    # The plate is modeled as opening a one-cell route past a parked crate.
    if state.crate != level.plate:
        return False
    return state.player + step == state.crate and in_bounds(level, state.player + 2 * step)


def slide_crate_east(crate: int, player: int, level: Level) -> Tuple[int, int]:
    wear = 0
    while crate in level.ice:
        next_crate = crate + 1
        if not in_bounds(level, next_crate) or next_crate == player:
            break
        crate = next_crate
        wear += 1
    return crate, wear


def move_conveyor(crate: int, player: int, dial: int, level: Level) -> int:
    if level.conveyor is None or crate != level.conveyor:
        return crate
    if dial == DIALS.index("E"):
        delta = 1
    elif dial == DIALS.index("W"):
        delta = -1
    else:
        return crate
    next_crate = crate + delta
    if not in_bounds(level, next_crate) or next_crate == player:
        return crate
    return next_crate


def apply_command(state: State, command: str, level: Level) -> Optional[Tuple[Optional[State], int, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    push_cost = 0

    if command == "move east":
        target = player + 1
        if target == crate:
            if can_cross_plate(state, level, 1):
                target = player + 2
            else:
                return None
        if not in_bounds(level, target):
            return None
        player = target
    elif command == "move west":
        target = player - 1
        if target == crate:
            if can_cross_plate(state, level, -1):
                target = player - 2
            else:
                return None
        if not in_bounds(level, target):
            return None
        player = target
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player + 1 != crate:
            return None
        next_crate = crate + 1
        if not in_bounds(level, next_crate) or next_crate == player:
            return None
        player += 1
        crate = next_crate
        push_cost = 1
    elif command == "take key":
        if has_key or player != level.key_position:
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
        return None, 0, 0
    elif command == "wait":
        pass
    else:
        return None

    crate, wear = slide_crate_east(crate, player, level)
    crate = move_conveyor(crate, player, dial, level)
    return State(player=player, crate=crate, dial=dial, has_key=has_key), push_cost, wear


def solve(level: Level, start: State) -> List[str]:
    start_key = (0, 0, 0, ())
    frontier: List[Tuple[int, int, int, Tuple[int, ...], State]] = [(0, 0, 0, (), start)]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_key}
    best_solution: Optional[Tuple[int, int, int, Tuple[int, ...]]] = None

    while frontier:
        if best_solution is not None and frontier[0][:4] >= best_solution:
            break

        steps, pushes, wear, sequence, state = heapq.heappop(frontier)
        if best.get(state) != (steps, pushes, wear, sequence):
            continue

        for command in COMMANDS:
            result = apply_command(state, command, level)
            if result is None:
                continue

            command_index = COMMAND_INDEX[command]
            next_sequence = sequence + (command_index,)
            next_steps = steps + 1

            next_state, push_cost, extra_wear = result
            next_pushes = pushes + push_cost
            next_wear = wear + extra_wear

            if next_state is None:
                solution_key = (next_steps, next_pushes, next_wear, next_sequence)
                if best_solution is None or solution_key < best_solution:
                    best_solution = solution_key
                continue

            next_key = (next_steps, next_pushes, next_wear, next_sequence)
            if next_key < best.get(next_state, (sys.maxsize, sys.maxsize, sys.maxsize, tuple())):
                best[next_state] = next_key
                heapq.heappush(frontier, (next_steps, next_pushes, next_wear, next_sequence, next_state))

    if best_solution is None:
        raise RuntimeError("No solution found")
    return [COMMANDS[index] for index in best_solution[3]]


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
