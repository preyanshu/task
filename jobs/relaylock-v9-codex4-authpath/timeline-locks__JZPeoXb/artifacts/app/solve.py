#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}
COMMANDS = tuple(
    sorted(
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
)


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
    ice: frozenset[int]
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
        target_dial=DIAL_TO_INDEX[raw["target_dial"]],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIAL_TO_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def route_open(level: Level, state: State) -> bool:
    return state.crate == level.plate


def can_player_enter(level: Level, state: State, destination: int) -> bool:
    if destination < 0 or destination >= level.length:
        return False
    if destination == state.crate:
        return False
    if destination == level.key_position and not route_open(level, state):
        return False
    return True


def apply_primary_action(level: Level, state: State, command: str) -> Optional[Tuple[State, bool]]:
    if command == "move east":
        destination = state.player + 1
        if not can_player_enter(level, state, destination):
            return None
        return State(destination, state.crate, state.dial, state.has_key), False

    if command == "move west":
        destination = state.player - 1
        if not can_player_enter(level, state, destination):
            return None
        return State(destination, state.crate, state.dial, state.has_key), False

    if command == "turn clockwise":
        return State(state.player, state.crate, (state.dial + 1) % 4, state.has_key), False

    if command == "turn counterclockwise":
        return State(state.player, state.crate, (state.dial - 1) % 4, state.has_key), False

    if command == "push east":
        if state.player != state.crate - 1:
            return None
        next_crate = state.crate + 1
        if next_crate >= level.length:
            return None
        return State(state.player, next_crate, state.dial, state.has_key), True

    if command == "take key":
        if state.has_key or state.player != level.key_position:
            return None
        return State(state.player, state.crate, state.dial, True), False

    if command == "use key":
        if (
            state.player != level.goal
            or not state.has_key
            or state.crate != level.plate
            or state.dial != level.target_dial
        ):
            return None
        return state, False

    if command == "wait":
        return state, False

    raise ValueError(f"unknown command: {command}")


def apply_sliding(level: Level, state: State) -> Optional[Tuple[State, int]]:
    crate = state.crate
    wear = 0

    while crate in level.ice:
        next_crate = crate + 1
        if next_crate >= level.length or next_crate == state.player:
            return None
        if next_crate in level.ice:
            wear += 1
        crate = next_crate

    return State(state.player, crate, state.dial, state.has_key), wear


def apply_conveyor(level: Level, state: State) -> State:
    if level.conveyor is None or state.crate != level.conveyor:
        return state

    if state.dial == DIAL_TO_INDEX["E"]:
        delta = 1
    elif state.dial == DIAL_TO_INDEX["W"]:
        delta = -1
    else:
        return state

    next_crate = state.crate + delta
    if 0 <= next_crate < level.length and next_crate != state.player:
        return State(state.player, next_crate, state.dial, state.has_key)
    return state


def simulate(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    primary = apply_primary_action(level, state, command)
    if primary is None:
        return None
    after_primary, pushed = primary

    after_sliding = apply_sliding(level, after_primary)
    if after_sliding is None:
        return None
    after_slide_state, wear = after_sliding
    after_conveyor = apply_conveyor(level, after_slide_state)

    solved = (
        command == "use key"
        and after_conveyor.player == level.goal
        and after_conveyor.has_key
        and after_conveyor.crate == level.plate
        and after_conveyor.dial == level.target_dial
    )
    return after_conveyor, 1 if pushed else 0, wear, solved


def solve(level: Level, start: State) -> List[str]:
    start_sequence: Tuple[str, ...] = ()
    start_cost = (0, 0, 0, start_sequence)
    heap: List[Tuple[int, int, int, Tuple[str, ...], State]] = [(0, 0, 0, start_sequence, start)]
    best: Dict[State, Tuple[int, int, int, Tuple[str, ...]]] = {start: start_cost}

    while heap:
        steps, pushes, wear, sequence, state = heapq.heappop(heap)
        current_cost = (steps, pushes, wear, sequence)
        if best.get(state) != current_cost:
            continue

        for command in COMMANDS:
            outcome = simulate(level, state, command)
            if outcome is None:
                continue

            next_state, push_cost, wear_cost, solved = outcome
            next_sequence = sequence + (command,)
            next_cost = (
                steps + 1,
                pushes + push_cost,
                wear + wear_cost,
                next_sequence,
            )

            if solved:
                return list(next_sequence)

            previous = best.get(next_state)
            if previous is None or next_cost < previous:
                best[next_state] = next_cost
                heapq.heappush(heap, (next_cost[0], next_cost[1], next_cost[2], next_sequence, next_state))

    raise ValueError("level is unsolvable")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 /app/solve.py <level.json> <output.json>", file=sys.stderr)
        return 1

    level, start = load_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
