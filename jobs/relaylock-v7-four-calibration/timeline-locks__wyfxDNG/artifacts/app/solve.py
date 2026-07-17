#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


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


def rotate(dial: int, clockwise: bool) -> int:
    return (dial + (1 if clockwise else -1)) % len(DIALS)


def can_cross_key_route(level: Level, state: State, src: int, dst: int) -> bool:
    if state.crate == level.plate:
        return True
    left = level.key_position - 1
    if left < 0:
        return True
    return not ((src == left and dst == level.key_position) or (src == level.key_position and dst == left))


def move_crate(level: Level, player: int, crate: int, delta: int) -> Optional[Tuple[int, int]]:
    destination = crate + delta
    if not (0 <= destination < level.length):
        return None
    if destination == player:
        return None
    wear = 1 if destination in level.ice else 0
    return destination, wear


def apply_ice(level: Level, player: int, crate: int) -> Tuple[int, int]:
    wear = 0
    while crate in level.ice:
        moved = move_crate(level, player, crate, 1)
        if moved is None:
            break
        crate, extra_wear = moved
        wear += extra_wear
    return crate, wear


def apply_conveyor(level: Level, player: int, crate: int, dial: int) -> Tuple[int, int]:
    if level.conveyor is None or crate != level.conveyor:
        return crate, 0
    if DIALS[dial] == "E":
        moved = move_crate(level, player, crate, 1)
    elif DIALS[dial] == "W":
        moved = move_crate(level, player, crate, -1)
    else:
        moved = None
    if moved is None:
        return crate, 0
    return moved


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    pushes = 0
    wear = 0
    solved = False

    if command == "move east":
        destination = player + 1
        if not (0 <= destination < level.length):
            return None
        if destination == crate:
            return None
        if not can_cross_key_route(level, state, player, destination):
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if not (0 <= destination < level.length):
            return None
        if destination == crate:
            return None
        if not can_cross_key_route(level, state, player, destination):
            return None
        player = destination
    elif command == "turn clockwise":
        dial = rotate(dial, True)
    elif command == "turn counterclockwise":
        dial = rotate(dial, False)
    elif command == "push east":
        if player != crate - 1:
            return None
        moved = move_crate(level, player, crate, 1)
        if moved is None:
            return None
        crate, extra_wear = moved
        wear += extra_wear
        pushes += 1
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
        solved = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate, extra_wear = apply_ice(level, player, crate)
    wear += extra_wear

    crate, extra_wear = apply_conveyor(level, player, crate, dial)
    wear += extra_wear

    return State(player=player, crate=crate, dial=dial, has_key=has_key), pushes, wear, solved


def solve(level: Level, start: State) -> List[str]:
    start_cost = (0, 0, 0, ())
    queue: List[Tuple[Tuple[int, int, int, Tuple[int, ...]], State]] = [(start_cost, start)]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_cost}

    while queue:
        cost, state = heapq.heappop(queue)
        if best.get(state) != cost:
            continue

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue
            next_state, push_cost, wear_cost, solved = result
            next_path = cost[3] + (COMMAND_INDEX[command],)
            next_cost = (cost[0] + 1, cost[1] + push_cost, cost[2] + wear_cost, next_path)
            if solved:
                return [COMMANDS[index] for index in next_path]
            if next_cost < best.get(next_state, (10**18, 10**18, 10**18, (10**18,))):
                best[next_state] = next_cost
                heapq.heappush(queue, (next_cost, next_state))

    raise RuntimeError("level is unsolvable")


def parse_level(payload: dict) -> Tuple[Level, State]:
    start = payload["start"]
    level = Level(
        length=payload["length"],
        conveyor=payload["conveyor"],
        ice=frozenset(payload["ice"]),
        plate=payload["plate"],
        key_position=payload["key_position"],
        goal=payload["goal"],
        target_dial=DIAL_INDEX[payload["target_dial"]],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIAL_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit(f"usage: {argv[0]} <level.json> <output.json>")

    with open(argv[1], "r", encoding="utf-8") as infile:
        payload = json.load(infile)
    level, start = parse_level(payload)
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
