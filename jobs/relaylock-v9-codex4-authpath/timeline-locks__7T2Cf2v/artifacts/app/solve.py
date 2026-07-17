#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple


DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: idx for idx, dial in enumerate(DIALS)}

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


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
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
    solved: bool = False


def can_enter(level: Level, state: State, pos: int) -> bool:
    if not (0 <= pos < level.length):
        return False
    if pos == state.crate:
        return False
    if pos == level.key_position and state.crate != level.plate:
        return False
    return True


def apply_sliding(level: Level, player: int, crate: int) -> Tuple[int, int]:
    wear = 0
    while crate in level.ice:
        nxt = crate + 1
        if nxt >= level.length or nxt == player:
            break
        crate = nxt
        if crate in level.ice:
            wear += 1
    return crate, wear


def apply_conveyor(level: Level, player: int, crate: int, dial: int) -> int:
    if level.conveyor is None or crate != level.conveyor:
        return crate
    if dial == DIAL_TO_INDEX["E"]:
        nxt = crate + 1
    elif dial == DIAL_TO_INDEX["W"]:
        nxt = crate - 1
    else:
        return crate
    if 0 <= nxt < level.length and nxt != player:
        return nxt
    return crate


def step(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    solved = state.solved
    pushes = 0

    if solved:
        return None

    if command == "move east":
        nxt = player + 1
        if not can_enter(level, state, nxt):
            return None
        player = nxt
    elif command == "move west":
        nxt = player - 1
        if not can_enter(level, state, nxt):
            return None
        player = nxt
    elif command == "push east":
        if player + 1 != crate:
            return None
        nxt = crate + 1
        if nxt >= level.length:
            return None
        crate = nxt
        pushes = 1
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        has_key = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
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

    crate, wear = apply_sliding(level, player, crate)
    crate = apply_conveyor(level, player, crate, dial)

    return State(player, crate, dial, has_key, solved), pushes, wear


def solve(level_data: dict) -> Iterable[str]:
    level = Level(
        length=level_data["length"],
        conveyor=level_data["conveyor"],
        ice=frozenset(level_data["ice"]),
        plate=level_data["plate"],
        key_position=level_data["key_position"],
        goal=level_data["goal"],
        target_dial=DIAL_TO_INDEX[level_data["target_dial"]],
    )
    start_info = level_data["start"]
    start = State(
        player=start_info["player"],
        crate=start_info["crate"],
        dial=DIAL_TO_INDEX[start_info["dial"]],
        has_key=bool(start_info["key"]),
        solved=False,
    )

    heap = [(0, 0, 0, (), start)]
    best = {start: (0, 0, 0, ())}

    while heap:
        commands_used, pushes_used, wear_used, path, state = heapq.heappop(heap)
        if best.get(state) != (commands_used, pushes_used, wear_used, path):
            continue
        if state.solved:
            return [COMMANDS[idx] for idx in path]

        for idx, command in enumerate(COMMANDS):
            result = step(level, state, command)
            if result is None:
                continue
            next_state, push_cost, wear_cost = result
            next_cost = (
                commands_used + 1,
                pushes_used + push_cost,
                wear_used + wear_cost,
                path + (idx,),
            )
            if next_cost < best.get(next_state, (float("inf"),) * 4):
                best[next_state] = next_cost
                heapq.heappush(heap, (*next_cost, next_state))

    raise ValueError("level is unsolvable")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    with open(sys.argv[1], "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = list(solve(level_data))
    with open(sys.argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main()
