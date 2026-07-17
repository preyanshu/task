#!/usr/bin/env python3
import heapq
import json
import sys


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

DIAL_TO_INT = {"N": 0, "E": 1, "S": 2, "W": 3}
CW = (1, 2, 3, 0)
CCW = (3, 0, 1, 2)
SOLVED = ("__SOLVED__",)


class Level:
    def __init__(self, data):
        start = data["start"]
        self.length = int(data["length"])
        self.start_state = (
            int(start["player"]),
            int(start["crate"]),
            DIAL_TO_INT[start["dial"]],
            bool(start["key"]),
        )
        self.conveyor = data["conveyor"]
        if self.conveyor is not None:
            self.conveyor = int(self.conveyor)
        self.ice = frozenset(int(pos) for pos in data["ice"])
        self.plate = int(data["plate"])
        self.key_position = int(data["key_position"])
        self.goal = int(data["goal"])
        self.target_dial = DIAL_TO_INT[data["target_dial"]]


def can_player_enter(pos, crate, level):
    if pos < 0 or pos >= level.length:
        return False
    if pos == crate:
        return False
    if pos == level.key_position and crate != level.plate:
        return False
    return True


def apply_command(state, command, level):
    player, crate, dial, has_key = state
    pushes = 0
    wear = 0

    if command == "move east":
        destination = player + 1
        if not can_player_enter(destination, crate, level):
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if not can_player_enter(destination, crate, level):
            return None
        player = destination
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
        dial = CW[dial]
    elif command == "turn counterclockwise":
        dial = CCW[dial]
    elif command == "use key":
        if (
            player != level.goal
            or not has_key
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        return SOLVED, 0, 0
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    while crate in level.ice and crate + 1 < level.length and crate + 1 != player:
        crate += 1
        wear += 1

    if level.conveyor is not None and crate == level.conveyor and dial in (1, 3):
        destination = crate + (1 if dial == 1 else -1)
        if 0 <= destination < level.length and destination != player:
            crate = destination

    return (player, crate, dial, has_key), pushes, wear


def solve(level):
    start = level.start_state
    best = {start: (0, 0, 0, ())}
    heap = [(0, 0, 0, (), start)]

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        cost = (steps, pushes, wear, path)
        if best.get(state) != cost:
            continue
        if state == SOLVED:
            return [COMMANDS[index] for index in path]

        for index, command in enumerate(COMMANDS):
            result = apply_command(state, command, level)
            if result is None:
                continue
            next_state, extra_pushes, extra_wear = result
            next_path = path + (index,)
            next_cost = (
                steps + 1,
                pushes + extra_pushes,
                wear + extra_wear,
                next_path,
            )
            if next_cost < best.get(next_state, (float("inf"),)):
                best[next_state] = next_cost
                heapq.heappush(heap, (*next_cost, next_state))

    return []


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = solve(Level(level_data))

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
