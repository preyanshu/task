#!/usr/bin/env python3
import heapq
import json
import sys
from typing import Dict, List, Optional, Tuple


DIALS = "NESW"
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}

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

State = Tuple[int, int, int, bool]
Key = Tuple[int, int, int, Tuple[int, ...]]


class Level:
    def __init__(self, raw: Dict[str, object]) -> None:
        start = raw["start"]
        self.length = int(raw["length"])
        self.conveyor = raw["conveyor"]
        self.ice = set(raw["ice"])
        self.plate = int(raw["plate"])
        self.key_position = int(raw["key_position"])
        self.goal = int(raw["goal"])
        self.target_dial = DIAL_INDEX[str(raw["target_dial"])]
        self.start_state: State = (
            int(start["player"]),
            int(start["crate"]),
            DIAL_INDEX[str(start["dial"])],
            bool(start["key"]),
        )


def apply_command(level: Level, state: State, command_index: int) -> Optional[Tuple[State, int, int, bool]]:
    player, crate, dial, has_key = state
    command = COMMANDS[command_index]
    route_open = crate == level.plate
    push_count = 0
    used_key = False

    if command == "move east":
        destination = player + 1
        if destination >= level.length or destination == crate:
            return None
        if destination == level.key_position and not route_open:
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if destination < 0 or destination == crate:
            return None
        if destination == level.key_position and not route_open:
            return None
        player = destination
    elif command == "push east":
        if player + 1 != crate:
            return None
        destination = crate + 1
        if destination >= level.length:
            return None
        crate = destination
        push_count = 1
    elif command == "take key":
        if player != level.key_position or has_key:
            return None
        has_key = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "use key":
        if player != level.goal or not has_key or crate != level.plate or dial != level.target_dial:
            return None
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    wear = 0
    while crate in level.ice:
        destination = crate + 1
        if destination >= level.length or destination == player:
            break
        crate = destination
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if dial == DIAL_INDEX["E"]:
            destination = crate + 1
            if destination < level.length and destination != player:
                crate = destination
        elif dial == DIAL_INDEX["W"]:
            destination = crate - 1
            if destination >= 0 and destination != player:
                crate = destination

    solved = (
        used_key
        and player == level.goal
        and has_key
        and crate == level.plate
        and dial == level.target_dial
    )
    return (player, crate, dial, has_key), push_count, wear, solved


def solve(level: Level) -> List[str]:
    start = level.start_state
    start_key: Key = (0, 0, 0, ())
    best: Dict[State, Key] = {start: start_key}
    queue: List[Tuple[int, int, int, Tuple[int, ...], State]] = [(0, 0, 0, (), start)]

    while queue:
        commands_used, pushes_used, wear_used, path, state = heapq.heappop(queue)
        current_key = (commands_used, pushes_used, wear_used, path)
        if best.get(state) != current_key:
            continue

        for command_index in range(len(COMMANDS)):
            result = apply_command(level, state, command_index)
            if result is None:
                continue

            next_state, extra_pushes, extra_wear, solved = result
            next_path = path + (command_index,)
            next_key: Key = (
                commands_used + 1,
                pushes_used + extra_pushes,
                wear_used + extra_wear,
                next_path,
            )

            if solved:
                return [COMMANDS[index] for index in next_path]

            if next_key < best.get(next_state, (sys.maxsize, sys.maxsize, sys.maxsize, ())):
                best[next_state] = next_key
                heapq.heappush(
                    queue,
                    (next_key[0], next_key[1], next_key[2], next_key[3], next_state),
                )

    raise RuntimeError("level has no solution")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level_path, output_path = sys.argv[1], sys.argv[2]
    with open(level_path, "r", encoding="utf-8") as infile:
        level = Level(json.load(infile))

    commands = solve(level)

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main()
