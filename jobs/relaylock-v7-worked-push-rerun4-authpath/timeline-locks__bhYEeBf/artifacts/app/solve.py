#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


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

DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}
TURN_CLOCKWISE = {"N": "E", "E": "S", "S": "W", "W": "N"}
TURN_COUNTERCLOCKWISE = {"N": "W", "W": "S", "S": "E", "E": "N"}
DIR_DELTA = {"E": 1, "W": -1}
MOMENTUM_INDEX = {None: 0, "E": 1, "W": 2}
MOMENTUM_VALUE = {value: key for key, value in MOMENTUM_INDEX.items()}


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: str


State = Tuple[int, int, int, bool, int]
SearchKey = Tuple[int, int, int, Tuple[int, ...]]


def parse_level(data: Dict) -> Tuple[Level, State]:
    start = data["start"]
    level = Level(
        length=int(data["length"]),
        conveyor=data.get("conveyor"),
        ice=frozenset(int(pos) for pos in data.get("ice", [])),
        plate=int(data["plate"]),
        key_position=int(data["key_position"]),
        goal=int(data["goal"]),
        target_dial=str(data["target_dial"]),
    )
    state = (
        int(start["player"]),
        int(start["crate"]),
        DIAL_INDEX[str(start["dial"])],
        bool(start["key"]),
        MOMENTUM_INDEX[None],
    )
    return level, state


def in_bounds(level: Level, pos: int) -> bool:
    return 0 <= pos < level.length


def plate_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def key_route_open(level: Level, crate: int, has_key: bool) -> bool:
    return has_key or plate_open(level, crate)


def move_player(level: Level, player: int, crate: int, has_key: bool, delta: int) -> Optional[int]:
    dest = player + delta
    if not in_bounds(level, dest):
        return None
    if dest == crate:
        return None
    if dest == level.key_position and not key_route_open(level, crate, has_key):
        return None
    return dest


def move_crate_one_step(
    level: Level, player: int, crate: int, direction: str, wear: int
) -> Optional[Tuple[int, int]]:
    delta = DIR_DELTA[direction]
    dest = crate + delta
    if not in_bounds(level, dest):
        return None
    if dest == player:
        return None
    if dest in level.ice:
        wear += 1
    return dest, wear


def apply_sliding(
    level: Level, player: int, crate: int, momentum: Optional[str], wear: int
) -> Optional[Tuple[int, int, Optional[str]]]:
    if momentum not in DIR_DELTA:
        return crate, wear, momentum
    while crate in level.ice:
        moved = move_crate_one_step(level, player, crate, momentum, wear)
        if moved is None:
            return None
        crate, wear = moved
    return crate, wear, momentum


def apply_conveyor(
    level: Level, player: int, crate: int, dial: str, wear: int, momentum: Optional[str]
) -> Optional[Tuple[int, int, Optional[str]]]:
    if level.conveyor is None or crate != level.conveyor:
        return crate, wear, momentum
    direction = dial if dial in DIR_DELTA else None
    if direction is None:
        return crate, wear, momentum
    moved = move_crate_one_step(level, player, crate, direction, wear)
    if moved is None:
        return None
    crate, wear = moved
    return crate, wear, direction


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    player, crate, dial_index, has_key, momentum_index = state
    dial = DIALS[dial_index]
    momentum = MOMENTUM_VALUE[momentum_index]
    wear = 0
    pushes = 0
    take_key = False
    used_key = False

    if command == "move east":
        moved = move_player(level, player, crate, has_key, 1)
        if moved is None:
            return None
        player = moved
    elif command == "move west":
        moved = move_player(level, player, crate, has_key, -1)
        if moved is None:
            return None
        player = moved
    elif command == "turn clockwise":
        dial = TURN_CLOCKWISE[dial]
    elif command == "turn counterclockwise":
        dial = TURN_COUNTERCLOCKWISE[dial]
    elif command == "push east":
        if player + 1 != crate:
            return None
        moved = move_crate_one_step(level, player, crate, "E", wear)
        if moved is None:
            return None
        crate, wear = moved
        momentum = "E"
        pushes = 1
    elif command == "take key":
        if has_key or player != level.key_position or not key_route_open(level, crate, has_key):
            return None
        take_key = True
    elif command == "use key":
        if (
            not has_key
            or player != level.goal
            or not plate_open(level, crate)
            or dial != level.target_dial
        ):
            return None
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    slid = apply_sliding(level, player, crate, momentum, wear)
    if slid is None:
        return None
    crate, wear, momentum = slid

    conveyed = apply_conveyor(level, player, crate, dial, wear, momentum)
    if conveyed is None:
        return None
    crate, wear, momentum = conveyed

    if take_key:
        if player != level.key_position or not key_route_open(level, crate, has_key):
            return None
        has_key = True

    solved = (
        used_key
        and player == level.goal
        and has_key
        and plate_open(level, crate)
        and dial == level.target_dial
    )

    next_state = (
        player,
        crate,
        DIAL_INDEX[dial],
        has_key,
        MOMENTUM_INDEX[momentum],
    )
    return next_state, pushes, wear, solved


def solve(level: Level, start: State) -> List[str]:
    initial_key: SearchKey = (0, 0, 0, ())
    heap: List[Tuple[SearchKey, State]] = [(initial_key, start)]
    best: Dict[State, SearchKey] = {start: initial_key}

    while heap:
        search_key, state = heapq.heappop(heap)
        if best.get(state) != search_key:
            continue
        commands_used, pushes_used, wear_used, path = search_key

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue
            next_state, push_cost, wear_cost, solved = result
            next_path = path + (COMMAND_INDEX[command],)
            next_key: SearchKey = (
                commands_used + 1,
                pushes_used + push_cost,
                wear_used + wear_cost,
                next_path,
            )
            if solved:
                return [COMMANDS[index] for index in next_path]
            if next_key < best.get(next_state, (10**18, 10**18, 10**18, (10**18,))):
                best[next_state] = next_key
                heapq.heappush(heap, (next_key, next_state))

    raise RuntimeError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    with open(argv[1], "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    level, start = parse_level(level_data)
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
