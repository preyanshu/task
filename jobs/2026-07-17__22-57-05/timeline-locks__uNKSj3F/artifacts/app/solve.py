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
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}


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


def parse_level(data: dict) -> Tuple[Level, State]:
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


def in_bounds(level: Level, pos: int) -> bool:
    return 0 <= pos < level.length


def key_route_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def can_player_enter(level: Level, crate: int, pos: int) -> bool:
    if not in_bounds(level, pos):
        return False
    if pos == crate:
        return False
    if pos == level.key_position and not key_route_open(level, crate):
        return False
    return True


def apply_post_phases(level: Level, player: int, crate: int, dial: int) -> Tuple[int, int]:
    wear = 0

    while crate in level.ice:
        next_crate = crate + 1
        if not in_bounds(level, next_crate) or next_crate == player:
            break
        crate = next_crate
        wear += 1

    if level.conveyor is not None and crate == level.conveyor and dial in (1, 3):
        delta = 1 if dial == 1 else -1
        next_crate = crate + delta
        if in_bounds(level, next_crate) and next_crate != player:
            crate = next_crate

    return crate, wear


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    push_cost = 0

    if command == "move east":
        next_player = player + 1
        if not can_player_enter(level, crate, next_player):
            return None
        player = next_player
    elif command == "move west":
        next_player = player - 1
        if not can_player_enter(level, crate, next_player):
            return None
        player = next_player
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player + 1 != crate:
            return None
        next_crate = crate + 1
        if not in_bounds(level, next_crate):
            return None
        crate = next_crate
        push_cost = 1
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
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate, wear = apply_post_phases(level, player, crate, dial)
    solved = (
        command == "use key"
        and player == level.goal
        and has_key
        and crate == level.plate
        and dial == level.target_dial
    )
    return State(player=player, crate=crate, dial=dial, has_key=has_key), push_cost, wear, solved


def solve(level: Level, start: State) -> List[str]:
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: (0, 0, 0, ())}
    heap: List[Tuple[int, int, int, Tuple[int, ...], int, Optional[State]]] = []
    serial = 0
    heapq.heappush(heap, (0, 0, 0, (), serial, start))
    serial += 1

    while heap:
        steps, pushes, wear, path, _, state = heapq.heappop(heap)
        if state is None:
            return [COMMANDS[index] for index in path]

        if best.get(state) != (steps, pushes, wear, path):
            continue

        for command_index, command in enumerate(COMMANDS):
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, push_cost, wear_cost, solved = result
            next_steps = steps + 1
            next_pushes = pushes + push_cost
            next_wear = wear + wear_cost
            next_path = path + (command_index,)

            if solved:
                heapq.heappush(
                    heap,
                    (next_steps, next_pushes, next_wear, next_path, serial, None),
                )
                serial += 1
                continue

            next_best = (next_steps, next_pushes, next_wear, next_path)
            current_best = best.get(next_state)
            if current_best is not None and current_best <= next_best:
                continue
            best[next_state] = next_best
            heapq.heappush(
                heap,
                (next_steps, next_pushes, next_wear, next_path, serial, next_state),
            )
            serial += 1

    raise RuntimeError("level is unsolvable")


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    with open(sys.argv[1], "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    level, start = parse_level(level_data)
    commands = solve(level, start)

    with open(sys.argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
