#!/usr/bin/env python3
import heapq
import json
import sys
from itertools import count
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
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}


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


def parse_level(data: Dict) -> Tuple[Level, State]:
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


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def key_route_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def can_enter(level: Level, destination: int, crate: int) -> bool:
    if not in_bounds(level, destination):
        return False
    if destination == crate:
        return False
    if destination == level.key_position and not key_route_open(level, crate):
        return False
    return True


def apply_primary(level: Level, state: State, command: str) -> Optional[Tuple[State, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    pushes = 0
    used_key = False

    if command == "move east":
        destination = player + 1
        if not can_enter(level, destination, crate):
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if not can_enter(level, destination, crate):
            return None
        player = destination
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player + 1 != crate:
            return None
        destination = crate + 1
        if not in_bounds(level, destination):
            return None
        crate = destination
        pushes = 1
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        has_key = True
    elif command == "use key":
        if (
            player != level.goal
            or not has_key
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    return State(player=player, crate=crate, dial=dial, has_key=has_key), pushes, used_key


def apply_post_phases(level: Level, state: State) -> Optional[Tuple[State, int]]:
    player = state.player
    crate = state.crate
    wear = 0

    while crate in level.ice:
        destination = crate + 1
        if not in_bounds(level, destination) or destination == player:
            return None
        crate = destination
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        direction = 0
        if state.dial == DIAL_INDEX["E"]:
            direction = 1
        elif state.dial == DIAL_INDEX["W"]:
            direction = -1
        if direction:
            destination = crate + direction
            if in_bounds(level, destination) and destination != player:
                crate = destination

    return State(player=player, crate=crate, dial=state.dial, has_key=state.has_key), wear


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    primary = apply_primary(level, state, command)
    if primary is None:
        return None

    after_primary, pushes, used_key = primary
    after_phases = apply_post_phases(level, after_primary)
    if after_phases is None:
        return None

    next_state, wear = after_phases
    return next_state, pushes, wear, used_key


def solve(level: Level, start: State) -> List[str]:
    start_cost = (0, 0, 0, ())
    ticket = count()
    heap: List[Tuple[Tuple[int, int, int, Tuple[str, ...]], int, State]] = [
        (start_cost, next(ticket), start)
    ]
    best: Dict[State, Tuple[int, int, int, Tuple[str, ...]]] = {start: start_cost}

    while heap:
        cost, _, state = heapq.heappop(heap)
        if best.get(state) != cost:
            continue

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, pushes, wear, used_key = result
            next_cost = (
                cost[0] + 1,
                cost[1] + pushes,
                cost[2] + wear,
                cost[3] + (command,),
            )

            if used_key:
                return list(next_cost[3])

            previous = best.get(next_state)
            if previous is None or next_cost < previous:
                best[next_state] = next_cost
                heapq.heappush(heap, (next_cost, next(ticket), next_state))

    raise RuntimeError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    with open(argv[1], "r", encoding="utf-8") as infile:
        data = json.load(infile)

    level, start = parse_level(data)
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
