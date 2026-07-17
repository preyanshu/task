#!/usr/bin/env python3
import heapq
import itertools
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
CW = {"N": "E", "E": "S", "S": "W", "W": "N"}
CCW = {value: key for key, value in CW.items()}

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


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: str


def parse_level(path: str) -> Tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    start = data["start"]
    level = Level(
        length=int(data["length"]),
        conveyor=data["conveyor"],
        ice=frozenset(int(value) for value in data["ice"]),
        plate=int(data["plate"]),
        key_position=int(data["key_position"]),
        goal=int(data["goal"]),
        target_dial=str(data["target_dial"]),
    )
    state = State(
        player=int(start["player"]),
        crate=int(start["crate"]),
        dial=str(start["dial"]),
        has_key=bool(start["key"]),
    )
    return level, state


def in_bounds(level: Level, position: int) -> bool:
    return 0 <= position < level.length


def try_move_crate(
    level: Level,
    player: int,
    crate: int,
    delta: int,
    wear: int,
) -> Optional[Tuple[int, int]]:
    new_crate = crate + delta
    if not in_bounds(level, new_crate) or new_crate == player:
        return None
    if new_crate in level.ice:
        wear += 1
    return new_crate, wear


def apply_sliding(level: Level, player: int, crate: int, wear: int) -> Optional[Tuple[int, int]]:
    while crate in level.ice:
        moved = try_move_crate(level, player, crate, 1, wear)
        if moved is None:
            return None
        crate, wear = moved
    return crate, wear


def apply_conveyor(level: Level, player: int, crate: int, wear: int, dial: str) -> Optional[Tuple[int, int]]:
    if level.conveyor is None or crate != level.conveyor:
        return crate, wear
    delta = 1 if dial == "E" else -1 if dial == "W" else 0
    if delta == 0:
        return crate, wear
    return try_move_crate(level, player, crate, delta, wear)


def is_use_key_solved(level: Level, state: State) -> bool:
    return (
        state.player == level.goal
        and state.has_key
        and state.crate == level.plate
        and state.dial == level.target_dial
    )


def transition(level: Level, state: State, command: str) -> Optional[Tuple[Optional[State], int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    wear = 0
    used_key = False

    if command == "move east":
        new_player = player + 1
        if not in_bounds(level, new_player) or new_player == crate:
            return None
        player = new_player
    elif command == "move west":
        new_player = player - 1
        if not in_bounds(level, new_player) or new_player == crate:
            return None
        player = new_player
    elif command == "turn clockwise":
        dial = CW[dial]
    elif command == "turn counterclockwise":
        dial = CCW[dial]
    elif command == "push east":
        if player + 1 != crate:
            return None
        moved = try_move_crate(level, player, crate, 1, wear)
        if moved is None:
            return None
        crate, wear = moved
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        has_key = True
    elif command == "use key":
        if not is_use_key_solved(level, state):
            return None
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    slid = apply_sliding(level, player, crate, wear)
    if slid is None:
        return None
    crate, wear = slid

    conveyed = apply_conveyor(level, player, crate, wear, dial)
    if conveyed is None:
        return None
    crate, wear = conveyed

    if used_key:
        return None, wear, True

    return State(player=player, crate=crate, dial=dial, has_key=has_key), wear, False


def solve(level: Level, start: State) -> List[str]:
    start_path: Tuple[int, ...] = ()
    start_cost = (0, 0, 0, start_path)
    counter = itertools.count()
    queue: List[Tuple[Tuple[int, int, int, Tuple[int, ...]], int, State]] = [
        (start_cost, next(counter), start)
    ]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_cost}

    while queue:
        cost, _, state = heapq.heappop(queue)
        if best.get(state) != cost:
            continue

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, wear_gain, solved = result
            index = COMMAND_INDEX[command]
            next_path = cost[3] + (index,)
            next_cost = (
                cost[0] + 1,
                cost[1] + (1 if command == "push east" else 0),
                cost[2] + wear_gain,
                next_path,
            )

            if solved:
                return [COMMANDS[value] for value in next_path]

            assert next_state is not None
            if next_cost < best.get(next_state, (10**18, 10**18, 10**18, (10**18,))):
                best[next_state] = next_cost
                heapq.heappush(queue, (next_cost, next(counter), next_state))

    raise RuntimeError("no solution found")


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
