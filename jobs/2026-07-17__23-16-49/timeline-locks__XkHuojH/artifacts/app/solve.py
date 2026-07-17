#!/usr/bin/env python3

import heapq
import json
import sys
from dataclasses import dataclass
from typing import Optional


NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

DIAL_FROM_TEXT = {"N": NORTH, "E": EAST, "S": SOUTH, "W": WEST}
DIAL_TO_TEXT = {value: key for key, value in DIAL_FROM_TEXT.items()}

LEX_COMMANDS = [
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
class State:
    player: int
    crate: int
    dial: int
    has_key: bool


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset[int]
    plate: int
    key_position: int
    goal: int
    target_dial: int
    start: State

    @classmethod
    def from_json(cls, data: dict) -> "Level":
        start = data["start"]
        return cls(
            length=data["length"],
            conveyor=data["conveyor"],
            ice=frozenset(data["ice"]),
            plate=data["plate"],
            key_position=data["key_position"],
            goal=data["goal"],
            target_dial=DIAL_FROM_TEXT[data["target_dial"]],
            start=State(
                player=start["player"],
                crate=start["crate"],
                dial=DIAL_FROM_TEXT[start["dial"]],
                has_key=bool(start["key"]),
            ),
        )


def can_enter(level: Level, state: State, destination: int) -> bool:
    if not 0 <= destination < level.length:
        return False
    if destination == state.crate:
        return False
    if destination == level.key_position and state.crate != level.plate:
        return False
    return True


def apply_post_phases(level: Level, player: int, crate: int, dial: int) -> tuple[int, int]:
    wear = 0

    while crate in level.ice:
        next_crate = crate + 1
        if next_crate >= level.length or next_crate == player:
            break
        crate = next_crate
        wear += 1

    if level.conveyor is not None and crate == level.conveyor and dial in (EAST, WEST):
        step = 1 if dial == EAST else -1
        next_crate = crate + step
        if 0 <= next_crate < level.length and next_crate != player:
            crate = next_crate

    return crate, wear


def transition(level: Level, state: State, command: str) -> tuple[Optional[State], int, bool]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    attempted_use = False

    if command == "move east":
        destination = player + 1
        if not can_enter(level, state, destination):
            return None, 0, False
        player = destination
    elif command == "move west":
        destination = player - 1
        if not can_enter(level, state, destination):
            return None, 0, False
        player = destination
    elif command == "push east":
        if player != crate - 1:
            return None, 0, False
        next_crate = crate + 1
        if next_crate >= level.length:
            return None, 0, False
        crate = next_crate
    elif command == "take key":
        if has_key or player != level.key_position:
            return None, 0, False
        has_key = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "use key":
        if not (
            player == level.goal
            and has_key
            and crate == level.plate
            and dial == level.target_dial
        ):
            return None, 0, False
        attempted_use = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate, wear = apply_post_phases(level, player, crate, dial)
    next_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
    solved = attempted_use and next_state.crate == level.plate
    return next_state, wear, solved


def solve(level: Level) -> list[str]:
    start = level.start
    start_path: tuple[int, ...] = ()
    start_cost = (0, 0, 0, start_path)
    heap: list[tuple[int, int, int, tuple[int, ...], int, Optional[State]]] = [
        (0, 0, 0, start_path, 0, start)
    ]
    best: dict[State, tuple[int, int, int, tuple[int, ...]]] = {start: start_cost}

    while heap:
        steps, pushes, wear, path, terminal, state = heapq.heappop(heap)
        if terminal:
            return [LEX_COMMANDS[i] for i in path]

        cost = (steps, pushes, wear, path)
        if best.get(state) != cost:
            continue

        for index, command in enumerate(LEX_COMMANDS):
            next_state, added_wear, solved = transition(level, state, command)
            if next_state is None:
                continue

            next_path = path + (index,)
            next_cost = (
                steps + 1,
                pushes + (1 if command == "push east" else 0),
                wear + added_wear,
                next_path,
            )

            if solved:
                heapq.heappush(heap, (*next_cost, 1, None))
                continue

            best_cost = best.get(next_state)
            if best_cost is None or next_cost < best_cost:
                best[next_state] = next_cost
                heapq.heappush(heap, (*next_cost, 0, next_state))

    raise RuntimeError("level is unsolvable")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = solve(Level.from_json(level_data))

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main()
