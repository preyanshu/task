#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple


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

DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}
INDEX_TO_DIAL = {index: dial for index, dial in enumerate(DIALS)}
EAST = 1
WEST = -1
NONE = 0
SOLVED = object()


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: FrozenSet[int]
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
    crate_dir: int


def parse_level(path: str) -> Tuple[Level, State]:
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
        crate_dir=NONE,
    )
    return level, state


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def move_crate(level: Level, player: int, crate: int, delta: int) -> Tuple[int, int]:
    target = crate + delta
    if not in_bounds(level, target) or target == player:
        return crate, 0
    wear = 1 if target in level.ice else 0
    return target, wear


def simulate(level: Level, state: State, command: str):
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    crate_dir = state.crate_dir
    pushes = 0
    wear = 0
    attempt_take = False
    attempt_use = False

    if command == "move east":
        target = player + 1
        if not in_bounds(level, target) or target == crate:
            return None
        player = target
    elif command == "move west":
        target = player - 1
        if not in_bounds(level, target) or target == crate:
            return None
        player = target
    elif command == "push east":
        if player + 1 != crate:
            return None
        target = crate + 1
        if not in_bounds(level, target) or target == player:
            return None
        crate = target
        crate_dir = EAST
        pushes = 1
        if crate in level.ice:
            wear += 1
    elif command == "take key":
        if player != level.key_position or has_key:
            return None
        attempt_take = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "use key":
        if player != level.goal or not has_key:
            return None
        attempt_use = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    while crate in level.ice and crate_dir in (EAST, WEST):
        next_crate, slide_wear = move_crate(level, player, crate, crate_dir)
        if next_crate == crate:
            break
        crate = next_crate
        wear += slide_wear

    if level.conveyor is not None and crate == level.conveyor:
        if INDEX_TO_DIAL[dial] == "E":
            conveyor_dir = EAST
        elif INDEX_TO_DIAL[dial] == "W":
            conveyor_dir = WEST
        else:
            conveyor_dir = NONE

        if conveyor_dir:
            next_crate, conveyor_wear = move_crate(level, player, crate, conveyor_dir)
            if next_crate != crate:
                crate = next_crate
                crate_dir = conveyor_dir
                wear += conveyor_wear

    plate_active = crate == level.plate

    if attempt_take:
        if not plate_active:
            return None
        has_key = True

    if attempt_use:
        if not plate_active or dial != level.target_dial:
            return None
        return SOLVED, pushes, wear

    return State(player=player, crate=crate, dial=dial, has_key=has_key, crate_dir=crate_dir), pushes, wear


def solve(level: Level, start: State) -> List[str]:
    heap: List[Tuple[int, int, int, Tuple[int, ...], object]] = []
    heapq.heappush(heap, (0, 0, 0, (), start))
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: (0, 0, 0, ())}

    while heap:
        steps, pushes, wear, path, node = heapq.heappop(heap)
        if node is SOLVED:
            return [COMMANDS[index] for index in path]

        state = node
        best_key = best.get(state)
        if best_key != (steps, pushes, wear, path):
            continue

        for index, command in enumerate(COMMANDS):
            outcome = simulate(level, state, command)
            if outcome is None:
                continue

            next_node, push_cost, wear_cost = outcome
            next_steps = steps + 1
            next_pushes = pushes + push_cost
            next_wear = wear + wear_cost
            next_path = path + (index,)

            if next_node is SOLVED:
                heapq.heappush(heap, (next_steps, next_pushes, next_wear, next_path, SOLVED))
                continue

            next_key = (next_steps, next_pushes, next_wear, next_path)
            previous = best.get(next_node)
            if previous is None or next_key < previous:
                best[next_node] = next_key
                heapq.heappush(heap, (next_steps, next_pushes, next_wear, next_path, next_node))

    raise RuntimeError("level is unsolvable")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level, start = parse_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
