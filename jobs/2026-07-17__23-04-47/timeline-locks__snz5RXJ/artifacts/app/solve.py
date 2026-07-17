#!/usr/bin/env python3
"""Canonical optimal solver for Relay-lock levels."""

from __future__ import annotations

import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


DIAL_TO_INDEX = {"N": 0, "E": 1, "S": 2, "W": 3}
INDEX_TO_DIAL = ("N", "E", "S", "W")

COMMANDS: Tuple[str, ...] = (
    "move east",
    "move west",
    "push east",
    "take key",
    "turn clockwise",
    "turn counterclockwise",
    "use key",
    "wait",
)


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset[int]
    plate: int
    key_position: int
    goal: int
    target_dial: int


State = Tuple[int, int, int, bool]
PathKey = Tuple[int, ...]
QueueEntry = Tuple[int, int, int, PathKey, Optional[State]]


def parse_level(raw: Dict[str, object]) -> Tuple[Level, State]:
    start = raw["start"]
    assert isinstance(start, dict)
    level = Level(
        length=int(raw["length"]),
        conveyor=None if raw["conveyor"] is None else int(raw["conveyor"]),
        ice=frozenset(int(pos) for pos in raw["ice"]),
        plate=int(raw["plate"]),
        key_position=int(raw["key_position"]),
        goal=int(raw["goal"]),
        target_dial=DIAL_TO_INDEX[str(raw["target_dial"])],
    )
    state: State = (
        int(start["player"]),
        int(start["crate"]),
        DIAL_TO_INDEX[str(start["dial"])],
        bool(start["key"]),
    )
    return level, state


def command_order() -> Iterable[Tuple[int, str]]:
    return enumerate(COMMANDS)


def can_enter_key_position(level: Level, crate: int) -> bool:
    return crate == level.plate


def apply_command(level: Level, state: State, command_index: int) -> Optional[Tuple[State, int, int, bool]]:
    player, crate, dial, has_key = state
    command = COMMANDS[command_index]
    pushes = 0
    use_key_attempt = False

    if command == "move east":
        dest = player + 1
        if dest >= level.length or dest == crate:
            return None
        if dest == level.key_position and not can_enter_key_position(level, crate):
            return None
        player = dest
    elif command == "move west":
        dest = player - 1
        if dest < 0 or dest == crate:
            return None
        if dest == level.key_position and not can_enter_key_position(level, crate):
            return None
        player = dest
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player != crate - 1:
            return None
        if crate + 1 >= level.length:
            return None
        crate += 1
        pushes = 1
    elif command == "take key":
        if player != level.key_position or has_key:
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
        use_key_attempt = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    wear = 0
    while crate in level.ice:
        nxt = crate + 1
        if nxt >= level.length or nxt == player:
            break
        crate = nxt
        wear += 1

    if level.conveyor is not None and crate == level.conveyor and dial in (1, 3):
        delta = 1 if dial == 1 else -1
        nxt = crate + delta
        if 0 <= nxt < level.length and nxt != player:
            crate = nxt

    new_state: State = (player, crate, dial, has_key)
    solved = (
        use_key_attempt
        and player == level.goal
        and has_key
        and crate == level.plate
        and dial == level.target_dial
    )
    return new_state, pushes, wear, solved


def solve(level: Level, start: State) -> List[str]:
    heap: List[QueueEntry] = [(0, 0, 0, (), start)]
    best: Dict[State, Tuple[int, int, int, PathKey]] = {start: (0, 0, 0, ())}

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if state is None:
            return [COMMANDS[index] for index in path]

        best_key = best.get(state)
        if best_key != (steps, pushes, wear, path):
            continue

        for command_index, _command in command_order():
            transition = apply_command(level, state, command_index)
            if transition is None:
                continue

            next_state, push_inc, wear_inc, solved = transition
            next_path = path + (command_index,)
            next_entry: QueueEntry = (
                steps + 1,
                pushes + push_inc,
                wear + wear_inc,
                next_path,
                None if solved else next_state,
            )

            if solved:
                heapq.heappush(heap, next_entry)
                continue

            next_key = next_entry[:4]
            prev_key = best.get(next_state)
            if prev_key is None or next_key < prev_key:
                best[next_state] = next_key
                heapq.heappush(heap, next_entry)

    raise RuntimeError("level is unsolvable")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 /app/solve.py <level.json> <output.json>", file=sys.stderr)
        return 2

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        raw_level = json.load(infile)

    level, start = parse_level(raw_level)
    commands = solve(level, start)

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
