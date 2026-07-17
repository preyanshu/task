#!/usr/bin/env python3
import heapq
import json
import sys
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
assert COMMANDS == sorted(COMMANDS)

DIAL_TO_INDEX = {"N": 0, "E": 1, "S": 2, "W": 3}
EAST = 1
WEST = -1
SOLVED = "SOLVED"


class Level:
    def __init__(self, raw: Dict[str, object]) -> None:
        self.length = int(raw["length"])
        start = raw["start"]
        self.start_player = int(start["player"])
        self.start_crate = int(start["crate"])
        self.start_dial = DIAL_TO_INDEX[str(start["dial"])]
        self.start_key = bool(start["key"])
        self.conveyor = raw["conveyor"]
        if self.conveyor is not None:
            self.conveyor = int(self.conveyor)
        self.ice = frozenset(int(cell) for cell in raw["ice"])
        self.plate = int(raw["plate"])
        self.key_position = int(raw["key_position"])
        self.goal = int(raw["goal"])
        self.target_dial = DIAL_TO_INDEX[str(raw["target_dial"])]

    def initial_state(self) -> Tuple[int, int, int, bool, int]:
        # The level schema has no explicit initial momentum field.
        slide_dir = EAST if self.start_crate in self.ice else 0
        return (
            self.start_player,
            self.start_crate,
            self.start_dial,
            self.start_key,
            slide_dir,
        )


def in_bounds(level: Level, pos: int) -> bool:
    return 0 <= pos < level.length


def route_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def slide_crate(
    level: Level,
    player: int,
    crate: int,
    slide_dir: int,
) -> Tuple[int, int, int]:
    wear = 0
    if crate not in level.ice:
        return crate, slide_dir, wear

    # When the crate is already on ice without a remembered direction,
    # default to east because the public rules expose no other seed value.
    direction = slide_dir if slide_dir in (EAST, WEST) else EAST
    while crate in level.ice:
        nxt = crate + direction
        if not in_bounds(level, nxt) or nxt == player:
            break
        crate = nxt
        if crate in level.ice:
            wear += 1
    return crate, direction, wear


def conveyor_move(
    level: Level,
    player: int,
    crate: int,
    slide_dir: int,
    dial: int,
) -> Tuple[int, int]:
    if level.conveyor is None or crate != level.conveyor:
        return crate, slide_dir
    if dial == DIAL_TO_INDEX["E"]:
        direction = EAST
    elif dial == DIAL_TO_INDEX["W"]:
        direction = WEST
    else:
        return crate, slide_dir

    nxt = crate + direction
    if not in_bounds(level, nxt) or nxt == player:
        return crate, slide_dir
    return nxt, direction


def transition(
    level: Level,
    state: Tuple[int, int, int, bool, int],
    command: str,
) -> Optional[Tuple[object, int, int]]:
    player, crate, dial, has_key, slide_dir = state
    pushes = 0

    if command == "move east":
        nxt = player + 1
        if not in_bounds(level, nxt) or nxt == crate:
            return None
        if nxt == level.key_position and not route_open(level, crate):
            return None
        player = nxt
    elif command == "move west":
        nxt = player - 1
        if not in_bounds(level, nxt) or nxt == crate:
            return None
        if nxt == level.key_position and not route_open(level, crate):
            return None
        player = nxt
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player + 1 != crate:
            return None
        nxt = crate + 1
        if not in_bounds(level, nxt):
            return None
        crate = nxt
        slide_dir = EAST
        pushes = 1
    elif command in ("take key", "use key", "wait"):
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate, slide_dir, wear = slide_crate(level, player, crate, slide_dir)
    crate, slide_dir = conveyor_move(level, player, crate, slide_dir, dial)

    if command == "take key":
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
        return SOLVED, pushes, wear

    return (player, crate, dial, has_key, slide_dir), pushes, wear


def solve(level: Level) -> List[str]:
    start = level.initial_state()
    start_cost = (0, 0, 0, ())
    best: Dict[object, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_cost}
    heap: List[Tuple[int, int, int, Tuple[int, ...], int, object]] = []
    counter = 0
    heapq.heappush(heap, (0, 0, 0, (), counter, start))

    while heap:
        steps, pushes, wear, path, _, state = heapq.heappop(heap)
        cost = (steps, pushes, wear, path)
        if best.get(state) != cost:
            continue
        if state == SOLVED:
            return [COMMANDS[index] for index in path]

        for index, command in enumerate(COMMANDS):
            result = transition(level, state, command)
            if result is None:
                continue
            next_state, add_pushes, add_wear = result
            next_path = path + (index,)
            next_cost = (
                steps + 1,
                pushes + add_pushes,
                wear + add_wear,
                next_path,
            )
            if next_cost < best.get(next_state, (10**18, 10**18, 10**18, (255,))):
                best[next_state] = next_cost
                counter += 1
                heapq.heappush(
                    heap,
                    (
                        next_cost[0],
                        next_cost[1],
                        next_cost[2],
                        next_cost[3],
                        counter,
                        next_state,
                    ),
                )

    raise ValueError("level is unsolvable")


def load_level(path: str) -> Level:
    with open(path, "r", encoding="utf-8") as infile:
        raw = json.load(infile)
    if isinstance(raw, dict) and "levels" in raw:
        levels = raw["levels"]
        if len(levels) != 1:
            raise ValueError("expected one level JSON object")
        raw = levels[0]
    return Level(raw)


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    level = load_level(argv[1])
    commands = solve(level)

    with open(argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
