#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple


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

DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}
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


def route_open(crate_pos: int, level: Level) -> bool:
    return crate_pos == level.plate


def apply_post_phases(
    player_pos: int,
    crate_pos: int,
    dial_index: int,
    level: Level,
) -> Tuple[int, int]:
    wear = 0

    while crate_pos in level.ice:
        next_pos = crate_pos + 1
        if next_pos >= level.length or next_pos == player_pos:
            break
        crate_pos = next_pos
        wear += 1

    if crate_pos == level.conveyor and DIALS[dial_index] in ("E", "W"):
        delta = 1 if DIALS[dial_index] == "E" else -1
        next_pos = crate_pos + delta
        if 0 <= next_pos < level.length and next_pos != player_pos:
            crate_pos = next_pos

    return crate_pos, wear


def step(
    state: Tuple[int, int, int, bool],
    command: str,
    level: Level,
) -> Optional[Tuple[object, int, int]]:
    player_pos, crate_pos, dial_index, has_key = state
    solved = False
    push_cost = 0

    if command == "move east":
        next_player = player_pos + 1
        if next_player >= level.length or next_player == crate_pos:
            return None
        if next_player == level.key_position and not route_open(crate_pos, level):
            return None
        player_pos = next_player
    elif command == "move west":
        next_player = player_pos - 1
        if next_player < 0 or next_player == crate_pos:
            return None
        if next_player == level.key_position and not route_open(crate_pos, level):
            return None
        player_pos = next_player
    elif command == "turn clockwise":
        dial_index = (dial_index + 1) % 4
    elif command == "turn counterclockwise":
        dial_index = (dial_index - 1) % 4
    elif command == "push east":
        if player_pos != crate_pos - 1:
            return None
        next_crate = crate_pos + 1
        if next_crate >= level.length:
            return None
        crate_pos = next_crate
        push_cost = 1
    elif command == "take key":
        if player_pos != level.key_position or has_key:
            return None
        has_key = True
    elif command == "use key":
        if (
            player_pos != level.goal
            or not has_key
            or crate_pos != level.plate
            or dial_index != level.target_dial
        ):
            return None
        solved = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate_pos, wear = apply_post_phases(player_pos, crate_pos, dial_index, level)

    if solved:
        return SOLVED, push_cost, wear
    return (player_pos, crate_pos, dial_index, has_key), push_cost, wear


def solve(level_data: dict) -> List[str]:
    level = Level(
        length=level_data["length"],
        conveyor=level_data["conveyor"],
        ice=frozenset(level_data["ice"]),
        plate=level_data["plate"],
        key_position=level_data["key_position"],
        goal=level_data["goal"],
        target_dial=DIAL_TO_INDEX[level_data["target_dial"]],
    )
    start = (
        level_data["start"]["player"],
        level_data["start"]["crate"],
        DIAL_TO_INDEX[level_data["start"]["dial"]],
        bool(level_data["start"]["key"]),
    )

    heap: List[Tuple[int, int, int, Tuple[int, ...], int, object]] = []
    best: Dict[object, Tuple[int, int, int, Tuple[int, ...]]] = {}
    serial = 0
    start_label = (0, 0, 0, ())
    best[start] = start_label
    heapq.heappush(heap, (*start_label, serial, start))
    serial += 1

    while heap:
        steps, pushes, wear, path, _, state = heapq.heappop(heap)
        label = (steps, pushes, wear, path)
        if best.get(state) != label:
            continue
        if state is SOLVED:
            return [COMMANDS[index] for index in path]

        for command_index, command in enumerate(COMMANDS):
            result = step(state, command, level)
            if result is None:
                continue
            next_state, push_delta, wear_delta = result
            next_label = (
                steps + 1,
                pushes + push_delta,
                wear + wear_delta,
                path + (command_index,),
            )
            if next_label < best.get(next_state, (sys.maxsize, sys.maxsize, sys.maxsize, (sys.maxsize,))):
                best[next_state] = next_label
                heapq.heappush(heap, (*next_label, serial, next_state))
                serial += 1

    raise RuntimeError("level is unsolvable")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python3 /app/solve.py <level.json> <output.json>", file=sys.stderr)
        return 1

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = solve(level_data)

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
