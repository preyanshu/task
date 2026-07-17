#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}

COMMANDS = tuple(
    sorted(
        (
            "move east",
            "move west",
            "turn clockwise",
            "turn counterclockwise",
            "push east",
            "take key",
            "use key",
            "wait",
        )
    )
)


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
        target_dial=DIAL_INDEX[raw["target_dial"]],
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


def can_bypass_plate(level: Level, state: State, delta: int) -> bool:
    if state.crate != level.plate:
        return False
    if delta == 1:
        return state.player == level.plate - 1 and in_bounds(level, level.plate + 1)
    if delta == -1:
        return state.player == level.plate + 1 and in_bounds(level, level.plate - 1)
    return False


def move_player(level: Level, state: State, delta: int) -> Optional[int]:
    if can_bypass_plate(level, state, delta):
        return state.player + 2 * delta

    target = state.player + delta
    if not in_bounds(level, target):
        return None
    if target == state.crate:
        return None
    return target


def slide_crate_east(level: Level, player: int, crate: int) -> Tuple[int, int]:
    wear = 0
    while crate in level.ice:
        nxt = crate + 1
        if not in_bounds(level, nxt) or nxt == player:
            break
        crate = nxt
        if crate in level.ice:
            wear += 1
    return crate, wear


def conveyor_move(level: Level, player: int, crate: int, dial: int) -> Tuple[int, int]:
    if level.conveyor is None or crate != level.conveyor:
        return crate, 0

    delta = 0
    if DIALS[dial] == "E":
        delta = 1
    elif DIALS[dial] == "W":
        delta = -1

    if delta == 0:
        return crate, 0

    nxt = crate + delta
    if not in_bounds(level, nxt) or nxt == player:
        return crate, 0
    return nxt, int(nxt in level.ice)


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    pushes = 0
    wear = 0
    used_key = False

    if command == "move east":
        nxt = move_player(level, state, 1)
        if nxt is None:
            return None
        player = nxt
    elif command == "move west":
        nxt = move_player(level, state, -1)
        if nxt is None:
            return None
        player = nxt
    elif command == "push east":
        if player != crate - 1:
            return None
        nxt = crate + 1
        if not in_bounds(level, nxt):
            return None
        crate = nxt
        pushes = 1
        wear += int(crate in level.ice)
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
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    slide_target, extra_wear = slide_crate_east(level, player, crate)
    crate = slide_target
    wear += extra_wear

    crate, extra_wear = conveyor_move(level, player, crate, dial)
    wear += extra_wear

    next_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
    return next_state, pushes, wear, used_key


def solve(level: Level, start: State) -> List[str]:
    start_path: Tuple[str, ...] = ()
    start_key = (0, 0, 0, start_path)

    queue: List[Tuple[int, int, int, Tuple[str, ...], State]] = []
    heapq.heappush(queue, (0, 0, 0, start_path, start))
    best: Dict[State, Tuple[int, int, int, Tuple[str, ...]]] = {start: start_key}

    while queue:
        steps, pushes, wear, path, state = heapq.heappop(queue)
        if best.get(state) != (steps, pushes, wear, path):
            continue

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue

            next_state, delta_pushes, delta_wear, used_key = result
            next_path = path + (command,)
            next_cost = (
                steps + 1,
                pushes + delta_pushes,
                wear + delta_wear,
                next_path,
            )

            if used_key:
                return list(next_path)

            current_best = best.get(next_state)
            if current_best is None or next_cost < current_best:
                best[next_state) = next_cost
                heapq.heappush(
                    queue,
                    (
                        next_cost[0],
                        next_cost[1],
                        next_cost[2],
                        next_cost[3],
                        next_state,
                    ),
                )

    raise RuntimeError("no solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)
    payload = {"commands": commands}
    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
