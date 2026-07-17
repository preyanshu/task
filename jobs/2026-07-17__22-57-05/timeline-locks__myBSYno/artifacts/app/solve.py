#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple


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

DIALS = "NESW"
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}
SOLVED_STATE = (-1, -1, -1, -1, -1)


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: int
    start_state: Tuple[int, int, int, bool]

    @classmethod
    def from_dict(cls, data: dict) -> "Level":
        start = data["start"]
        return cls(
            length=data["length"],
            conveyor=data["conveyor"],
            ice=frozenset(data["ice"]),
            plate=data["plate"],
            key_position=data["key_position"],
            goal=data["goal"],
            target_dial=DIAL_TO_INDEX[data["target_dial"]],
            start_state=(
                start["player"],
                start["crate"],
                DIAL_TO_INDEX[start["dial"]],
                bool(start["key"]),
            ),
        )


def route_open(level: Level, crate: int) -> bool:
    return crate == level.plate


def blocked_key_entry(level: Level, crate: int, destination: int) -> bool:
    return destination == level.key_position and not route_open(level, crate)


def apply_post_command_phases(
    level: Level, player: int, crate: int, dial: int
) -> Tuple[int, int]:
    wear = 0

    while crate in level.ice:
        nxt = crate + 1
        if nxt >= level.length or nxt == player:
            break
        crate = nxt
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if dial == DIAL_TO_INDEX["E"]:
            dst = crate + 1
            if dst < level.length and dst != player:
                crate = dst
        elif dial == DIAL_TO_INDEX["W"]:
            dst = crate - 1
            if dst >= 0 and dst != player:
                crate = dst

    return crate, wear


def transition(
    level: Level, state: Tuple[int, int, int, bool], command: str
) -> Optional[Tuple[Tuple[int, int, int, bool], int, int, bool]]:
    player, crate, dial, has_key = state
    pushes = 0
    used_key = False

    if command == "move east":
        dst = player + 1
        if dst >= level.length or dst == crate or blocked_key_entry(level, crate, dst):
            return None
        player = dst
    elif command == "move west":
        dst = player - 1
        if dst < 0 or dst == crate or blocked_key_entry(level, crate, dst):
            return None
        player = dst
    elif command == "push east":
        if player + 1 != crate or crate + 1 >= level.length:
            return None
        crate += 1
        pushes = 1
    elif command == "take key":
        if player != level.key_position or has_key:
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

    crate, wear = apply_post_command_phases(level, player, crate, dial)
    new_state = (player, crate, dial, has_key)
    solved = (
        used_key
        and player == level.goal
        and has_key
        and crate == level.plate
        and dial == level.target_dial
    )
    return new_state, pushes, wear, solved


def solve(level: Level) -> Iterable[str]:
    start = level.start_state
    start_key = (0, 0, 0, ())
    best: Dict[Tuple[int, ...], Tuple[int, int, int, Tuple[int, ...]]] = {start: start_key}
    heap = [(0, 0, 0, (), start)]

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if best.get(state) != (steps, pushes, wear, path):
            continue
        if state == SOLVED_STATE:
            return [COMMANDS[index] for index in path]

        for command_index, command in enumerate(COMMANDS):
            result = transition(level, state, command)
            if result is None:
                continue

            new_state, push_cost, wear_cost, solved = result
            new_path = path + (command_index,)
            new_key = (
                steps + 1,
                pushes + push_cost,
                wear + wear_cost,
                new_path,
            )
            next_state = SOLVED_STATE if solved else new_state

            previous = best.get(next_state)
            if previous is None or new_key < previous:
                best[next_state] = new_key
                heapq.heappush(heap, (*new_key, next_state))

    raise RuntimeError("level is unsolvable")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = list(solve(Level.from_dict(level_data)))

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main()
