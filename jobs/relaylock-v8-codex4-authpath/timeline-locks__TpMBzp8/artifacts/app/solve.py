#!/usr/bin/env python3
import heapq
import json
import sys


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

DIALS = ("N", "E", "S", "W")
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}
TERMINAL = object()


class Level:
    def __init__(self, data):
        self.length = data["length"]
        self.conveyor = data["conveyor"]
        self.ice = set(data["ice"])
        self.plate = data["plate"]
        self.key_position = data["key_position"]
        self.goal = data["goal"]
        self.target_dial = DIAL_TO_INDEX[data["target_dial"]]

        start = data["start"]
        self.start_state = (
            start["player"],
            start["crate"],
            DIAL_TO_INDEX[start["dial"]],
            bool(start["key"]),
        )

    def route_open(self, crate):
        return crate == self.plate

    def can_player_enter(self, destination, crate):
        if not (0 <= destination < self.length):
            return False
        if destination == crate:
            return False
        if destination == self.key_position and not self.route_open(crate):
            return False
        return True

    def apply_command(self, state, command):
        player, crate, dial, has_key = state
        push_cost = 0
        wear_cost = 0

        if command == "move east":
            destination = player + 1
            if not self.can_player_enter(destination, crate):
                return None
            player = destination
        elif command == "move west":
            destination = player - 1
            if not self.can_player_enter(destination, crate):
                return None
            player = destination
        elif command == "turn clockwise":
            dial = (dial + 1) % 4
        elif command == "turn counterclockwise":
            dial = (dial - 1) % 4
        elif command == "push east":
            if player + 1 != crate:
                return None
            destination = crate + 1
            if destination >= self.length:
                return None
            crate = destination
            push_cost = 1
        elif command == "take key":
            if player != self.key_position:
                return None
            has_key = True
        elif command == "use key":
            if (
                player == self.goal
                and has_key
                and crate == self.plate
                and dial == self.target_dial
            ):
                return TERMINAL, 0, 0
            return None
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        # Ice sliding is deterministic and resolves before conveyors.
        while crate in self.ice:
            destination = crate + 1
            if destination >= self.length or destination == player:
                break
            crate = destination
            if crate in self.ice:
                wear_cost += 1

        if self.conveyor is not None and crate == self.conveyor:
            if dial == DIAL_TO_INDEX["E"]:
                destination = crate + 1
            elif dial == DIAL_TO_INDEX["W"]:
                destination = crate - 1
            else:
                destination = None

            if (
                destination is not None
                and 0 <= destination < self.length
                and destination != player
            ):
                crate = destination

        return (player, crate, dial, has_key), push_cost, wear_cost


def solve(level):
    start = level.start_state
    best = {start: (0, 0, 0, ())}
    heap = [(0, 0, 0, (), start)]

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if state is TERMINAL:
            return list(path)

        if best.get(state) != (steps, pushes, wear, path):
            continue

        for command in COMMANDS:
            result = level.apply_command(state, command)
            if result is None:
                continue

            next_path = path + (command,)
            if result[0] is TERMINAL:
                next_item = (
                    steps + 1,
                    pushes + result[1],
                    wear + result[2],
                    next_path,
                    TERMINAL,
                )
                heapq.heappush(heap, next_item)
                continue

            next_state, push_cost, wear_cost = result
            next_key = (
                steps + 1,
                pushes + push_cost,
                wear + wear_cost,
                next_path,
            )
            if next_key < best.get(next_state, (float("inf"),)):
                best[next_state] = next_key
                heapq.heappush(heap, next_key + (next_state,))

    raise RuntimeError("level is unsolvable")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    with open(argv[1], "r", encoding="utf-8") as infile:
        level = Level(json.load(infile))

    commands = solve(level)

    with open(argv[2], "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps({"commands": commands}, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv)
