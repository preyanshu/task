#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


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
DIAL_CLOCKWISE = {"N": "E", "E": "S", "S": "W", "W": "N"}
DIAL_COUNTERCLOCKWISE = {value: key for key, value in DIAL_CLOCKWISE.items()}
CONVEYOR_DELTA = {"E": 1, "W": -1, "N": 0, "S": 0}


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: str


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


def load_level(path: str) -> Tuple[Level, State]:
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
        target_dial=data["target_dial"],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=start["dial"],
        has_key=bool(start["key"]),
    )
    return level, state


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def crate_on_plate(level: Level, state: State) -> bool:
    return state.crate == level.plate


def move_crate(level: Level, state: State, destination: int, wear: int) -> Optional[Tuple[State, int]]:
    if not in_bounds(level, destination):
        return None
    if destination == state.player:
        return None
    if destination in level.ice:
        wear += 1
    return State(state.player, destination, state.dial, state.has_key), wear


def apply_ice(level: Level, state: State, wear: int) -> Optional[Tuple[State, int]]:
    current = state
    total_wear = wear
    while current.crate in level.ice:
        moved = move_crate(level, current, current.crate + 1, total_wear)
        if moved is None:
            return None
        current, total_wear = moved
    return current, total_wear


def apply_conveyor(level: Level, state: State, wear: int) -> Optional[Tuple[State, int]]:
    if level.conveyor is None or state.crate != level.conveyor:
        return state, wear

    delta = CONVEYOR_DELTA[state.dial]
    if delta == 0:
        return state, wear

    moved = move_crate(level, state, state.crate + delta, wear)
    if moved is None:
        return state, wear
    return moved


def solve_check(level: Level, state: State, command: str) -> bool:
    return (
        command == "use key"
        and state.player == level.goal
        and state.has_key
        and crate_on_plate(level, state)
        and state.dial == level.target_dial
    )


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    push_cost = 1 if command == "push east" else 0
    wear = 0
    current = state

    if command == "move east":
        destination = current.player + 1
        if not in_bounds(level, destination) or destination == current.crate:
            return None
        current = State(destination, current.crate, current.dial, current.has_key)
    elif command == "move west":
        destination = current.player - 1
        if not in_bounds(level, destination) or destination == current.crate:
            return None
        current = State(destination, current.crate, current.dial, current.has_key)
    elif command == "turn clockwise":
        current = State(current.player, current.crate, DIAL_CLOCKWISE[current.dial], current.has_key)
    elif command == "turn counterclockwise":
        current = State(
            current.player,
            current.crate,
            DIAL_COUNTERCLOCKWISE[current.dial],
            current.has_key,
        )
    elif command == "push east":
        if current.player != current.crate - 1:
            return None
        moved = move_crate(level, current, current.crate + 1, wear)
        if moved is None:
            return None
        current, wear = moved
    elif command == "take key":
        if current.has_key or current.player != level.key_position or not crate_on_plate(level, current):
            return None
        current = State(current.player, current.crate, current.dial, True)
    elif command == "use key":
        if (
            current.player != level.goal
            or not current.has_key
            or not crate_on_plate(level, current)
            or current.dial != level.target_dial
        ):
            return None
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    iced = apply_ice(level, current, wear)
    if iced is None:
        return None
    current, wear = iced

    conveyed = apply_conveyor(level, current, wear)
    if conveyed is None:
        return None
    current, wear = conveyed

    return current, push_cost, wear, solve_check(level, current, command)


def search(level: Level, start: State) -> List[str]:
    start_key = (0, 0, 0, ())
    queue: List[Tuple[int, int, int, Tuple[int, ...], State]] = [
        (0, 0, 0, (), start)
    ]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_key}

    while queue:
        steps, pushes, wear, path, state = heapq.heappop(queue)
        best_key = best.get(state)
        if best_key != (steps, pushes, wear, path):
            continue

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, push_cost, extra_wear, solved = result
            next_path = path + (COMMAND_INDEX[command],)
            next_key = (
                steps + 1,
                pushes + push_cost,
                wear + extra_wear,
                next_path,
            )

            if solved:
                return [COMMANDS[index] for index in next_path]

            if next_key < best.get(next_state, (10**18, 10**18, 10**18, (10**18,))):
                best[next_state] = next_key
                heapq.heappush(
                    queue,
                    (next_key[0], next_key[1], next_key[2], next_key[3], next_state),
                )

    raise RuntimeError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("Usage: python3 solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = search(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
