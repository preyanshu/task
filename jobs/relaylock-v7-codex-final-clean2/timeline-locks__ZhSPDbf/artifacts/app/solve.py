#!/usr/bin/env python3
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

DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: idx for idx, dial in enumerate(DIALS)}
MOVE_DELTA = {"east": 1, "west": -1}


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

    level = Level(
        length=raw["length"],
        conveyor=raw["conveyor"],
        ice=frozenset(raw["ice"]),
        plate=raw["plate"],
        key_position=raw["key_position"],
        goal=raw["goal"],
        target_dial=DIAL_INDEX[raw["target_dial"]],
    )
    start = raw["start"]
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIAL_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def can_enter_player_cell(level: Level, state: State, target: int) -> bool:
    if not (0 <= target < level.length):
        return False
    if target == state.crate:
        return False
    if target == level.key_position and state.crate != level.plate:
        return False
    return True


def apply_primary(
    level: Level, state: State, command: str
) -> Optional[Tuple[State, int, bool]]:
    if command == "move east":
        target = state.player + MOVE_DELTA["east"]
        if not can_enter_player_cell(level, state, target):
            return None
        return State(target, state.crate, state.dial, state.has_key), 0, False

    if command == "move west":
        target = state.player + MOVE_DELTA["west"]
        if not can_enter_player_cell(level, state, target):
            return None
        return State(target, state.crate, state.dial, state.has_key), 0, False

    if command == "push east":
        if state.player + 1 != state.crate:
            return None
        target = state.crate + 1
        if not (0 <= target < level.length):
            return None
        if target == state.player:
            return None
        wear = 1 if target in level.ice else 0
        return State(state.player, target, state.dial, state.has_key), wear, False

    if command == "take key":
        if state.has_key or state.player != level.key_position:
            return None
        return State(state.player, state.crate, state.dial, True), 0, False

    if command == "turn clockwise":
        return (
            State(state.player, state.crate, (state.dial + 1) % 4, state.has_key),
            0,
            False,
        )

    if command == "turn counterclockwise":
        return (
            State(state.player, state.crate, (state.dial - 1) % 4, state.has_key),
            0,
            False,
        )

    if command == "use key":
        if (
            state.player == level.goal
            and state.has_key
            and state.crate == level.plate
            and state.dial == level.target_dial
        ):
            return state, 0, True
        return None

    if command == "wait":
        return state, 0, False

    raise ValueError(f"Unknown command: {command}")


def apply_automatic_phases(level: Level, state: State) -> Optional[Tuple[State, int]]:
    crate = state.crate
    wear = 0

    while crate in level.ice:
        target = crate + 1
        if not (0 <= target < level.length):
            return None
        if target == state.player:
            return None
        crate = target
        if crate in level.ice:
            wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        delta = 0
        if state.dial == DIAL_INDEX["E"]:
            delta = 1
        elif state.dial == DIAL_INDEX["W"]:
            delta = -1

        if delta:
            target = crate + delta
            if not (0 <= target < level.length):
                return None
            if target == state.player:
                return None
            crate = target
            if crate in level.ice:
                wear += 1

    return State(state.player, crate, state.dial, state.has_key), wear


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, bool]]:
    primary = apply_primary(level, state, command)
    if primary is None:
        return None

    after_primary, primary_wear, solved = primary
    if solved:
        return after_primary, primary_wear, True

    after_phases = apply_automatic_phases(level, after_primary)
    if after_phases is None:
        return None

    next_state, phase_wear = after_phases
    return next_state, primary_wear + phase_wear, False


def solve(level: Level, start: State) -> List[str]:
    frontier: Dict[State, Tuple[int, int, Tuple[int, ...]]] = {
        start: (0, 0, ())
    }
    seen_depth: Dict[State, int] = {start: 0}
    depth = 0

    while frontier:
        current_items = sorted(frontier.items(), key=lambda item: item[1][2])
        best_solution: Optional[Tuple[int, int, Tuple[int, ...]]] = None
        next_frontier: Dict[State, Tuple[int, int, Tuple[int, ...]]] = {}

        for state, (pushes, wear, path) in current_items:
            for cmd_index, command in enumerate(COMMANDS):
                result = transition(level, state, command)
                if result is None:
                    continue

                next_state, extra_wear, solved = result
                next_pushes = pushes + (1 if command == "push east" else 0)
                next_wear = wear + extra_wear
                next_path = path + (cmd_index,)
                key = (next_pushes, next_wear, next_path)

                if solved:
                    if best_solution is None or key < best_solution:
                        best_solution = key
                    continue

                next_depth = depth + 1
                prior_depth = seen_depth.get(next_state)
                if prior_depth is not None and prior_depth < next_depth:
                    continue

                previous = next_frontier.get(next_state)
                if previous is None or key < previous:
                    next_frontier[next_state] = key

        if best_solution is not None:
            return [COMMANDS[idx] for idx in best_solution[2]]

        depth += 1
        for state in next_frontier:
            seen_depth[state] = depth
        frontier = next_frontier

    raise RuntimeError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
