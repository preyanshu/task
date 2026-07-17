#!/usr/bin/env python3

import json
import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}

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
SOLVED = object()


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: int


State = Tuple[int, int, int, bool]
Transition = Tuple[object, int, int]


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
        target_dial=DIAL_TO_INDEX[raw["target_dial"]],
    )
    state = (
        start["player"],
        start["crate"],
        DIAL_TO_INDEX[start["dial"]],
        bool(start["key"]),
    )
    return level, state


def route_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def can_player_enter(level: Level, destination: int, crate: int) -> bool:
    if destination < 0 or destination >= level.length:
        return False
    if destination == crate:
        return False
    if destination == level.key_position and not route_open(level, crate):
        return False
    return True


def apply_sliding(level: Level, player: int, crate: int) -> Optional[Tuple[int, int]]:
    wear = 0
    while crate in level.ice:
        destination = crate + 1
        if destination >= level.length or destination == player:
            return None
        crate = destination
        wear += 1
    return crate, wear


def apply_conveyor(level: Level, player: int, crate: int, dial: int) -> int:
    if crate != level.conveyor:
        return crate
    if dial == DIAL_TO_INDEX["E"]:
        destination = crate + 1
    elif dial == DIAL_TO_INDEX["W"]:
        destination = crate - 1
    else:
        return crate
    if 0 <= destination < level.length and destination != player:
        return destination
    return crate


def transition(level: Level, state: State, command: str) -> Optional[Transition]:
    player, crate, dial, has_key = state
    next_player = player
    next_crate = crate
    next_dial = dial
    next_key = has_key
    push_count = 0
    solved = False

    if command == "move east":
        destination = player + 1
        if not can_player_enter(level, destination, crate):
            return None
        next_player = destination
    elif command == "move west":
        destination = player - 1
        if not can_player_enter(level, destination, crate):
            return None
        next_player = destination
    elif command == "turn clockwise":
        next_dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        next_dial = (dial - 1) % 4
    elif command == "push east":
        if player != crate - 1:
            return None
        destination = crate + 1
        if destination >= level.length:
            return None
        next_crate = destination
        push_count = 1
    elif command == "take key":
        if player != level.key_position:
            return None
        next_key = True
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
        return None

    sliding = apply_sliding(level, next_player, next_crate)
    if sliding is None:
        return None
    next_crate, wear = sliding
    next_crate = apply_conveyor(level, next_player, next_crate, next_dial)

    if solved:
        return SOLVED, push_count, wear
    return (next_player, next_crate, next_dial, next_key), push_count, wear


def solve(level: Level, start: State) -> List[str]:
    distances: Dict[State, int] = {start: 0}
    transitions: Dict[State, List[Tuple[str, Transition]]] = {}
    by_distance: List[List[State]] = [[start]]
    queue: deque[State] = deque([start])
    solution_depth: Optional[int] = None

    while queue:
        state = queue.popleft()
        depth = distances[state]
        if solution_depth is not None and depth >= solution_depth:
            continue

        state_transitions: List[Tuple[str, Transition]] = []
        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue
            target, push_count, wear = result
            state_transitions.append((command, (target, push_count, wear)))
            if target is SOLVED:
                if solution_depth is None:
                    solution_depth = depth + 1
                continue
            if target not in distances:
                next_depth = depth + 1
                distances[target] = next_depth
                if len(by_distance) <= next_depth:
                    by_distance.append([])
                by_distance[next_depth].append(target)
                queue.append(target)
        transitions[state] = state_transitions

    if solution_depth is None:
        raise ValueError("Level is unsolvable")

    best_state_cost: Dict[State, Tuple[int, int, Tuple[int, ...]]] = {start: (0, 0, ())}
    best_solution: Optional[Tuple[int, int, Tuple[int, ...]]] = None

    for depth in range(solution_depth):
        for state in by_distance[depth]:
            current = best_state_cost.get(state)
            if current is None:
                continue
            current_pushes, current_wear, current_path = current
            for command, (target, push_count, wear) in transitions[state]:
                next_path = current_path + (COMMAND_INDEX[command],)
                candidate = (
                    current_pushes + push_count,
                    current_wear + wear,
                    next_path,
                )
                if target is SOLVED:
                    if depth + 1 == solution_depth and (
                        best_solution is None or candidate < best_solution
                    ):
                        best_solution = candidate
                    continue
                if distances.get(target) != depth + 1:
                    continue
                previous = best_state_cost.get(target)
                if previous is None or candidate < previous:
                    best_state_cost[target] = candidate

    if best_solution is None:
        raise ValueError("No canonical solution found")

    return [COMMANDS[index] for index in best_solution[2]]


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit(f"Usage: {argv[0]} <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
