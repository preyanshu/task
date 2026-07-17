#!/usr/bin/env python3
import heapq
import json
import sys


COMMANDS = (
    "move east",
    "move west",
    "push east",
    "take key",
    "turn clockwise",
    "turn counterclockwise",
    "use key",
    "wait",
)

DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}


class Solver:
    def __init__(self, level):
        self.length = level["length"]
        start = level["start"]
        self.start_state = (
            start["player"],
            start["crate"],
            DIAL_INDEX[start["dial"]],
            bool(start["key"]),
        )
        self.conveyor = level["conveyor"]
        self.ice = frozenset(level["ice"])
        self.plate = level["plate"]
        self.key_position = level["key_position"]
        self.goal = level["goal"]
        self.target_dial = DIAL_INDEX[level["target_dial"]]

    def in_bounds(self, position):
        return 0 <= position < self.length

    def apply(self, state, command):
        player, crate, dial, has_key = state
        wear = 0
        push_count = 0

        solved = False

        if command == "move east":
            destination = player + 1
            if not self.in_bounds(destination):
                return None
            if destination == crate:
                return None
            if destination == self.key_position and crate != self.plate:
                return None
            player = destination
        elif command == "move west":
            destination = player - 1
            if not self.in_bounds(destination):
                return None
            if destination == crate:
                return None
            if destination == self.key_position and crate != self.plate:
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
            if not self.in_bounds(destination):
                return None
            crate = destination
            push_count = 1
        elif command == "take key":
            if has_key or player != self.key_position:
                return None
            has_key = True
        elif command == "use key":
            if (
                player == self.goal
                and has_key
                and crate == self.plate
                and dial == self.target_dial
            ):
                solved = True
            else:
                return None
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        while crate in self.ice:
            destination = crate + 1
            if not self.in_bounds(destination):
                return None
            crate = destination
            wear += 1

        if self.conveyor is not None and crate == self.conveyor and dial in (1, 3):
            delta = 1 if dial == 1 else -1
            destination = crate + delta
            if self.in_bounds(destination) and destination != player:
                crate = destination

        if solved:
            return ("SOLVED", push_count, wear)

        return ((player, crate, dial, has_key), push_count, wear)

    def solve(self):
        start_path = ()
        best = {self.start_state: (0, 0, 0, start_path)}
        queue = [(0, 0, 0, start_path, self.start_state)]

        while queue:
            steps, pushes, wear, path, state = heapq.heappop(queue)
            if state is None:
                return list(path)
            if best.get(state) != (steps, pushes, wear, path):
                continue

            for command in COMMANDS:
                result = self.apply(state, command)
                if result is None:
                    continue

                next_steps = steps + 1
                next_pushes = pushes + result[1]
                next_wear = wear + result[2]
                next_path = path + (command,)

                if result[0] == "SOLVED":
                    heapq.heappush(
                        queue,
                        (next_steps, next_pushes, next_wear, next_path, None),
                    )
                    continue

                next_state = result[0]
                candidate = (next_steps, next_pushes, next_wear, next_path)
                if candidate < best.get(next_state, (float("inf"),) * 4):
                    best[next_state] = candidate
                    heapq.heappush(
                        queue,
                        (next_steps, next_pushes, next_wear, next_path, next_state),
                    )

        raise RuntimeError("level is unsolvable")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level = json.load(infile)

    commands = Solver(level).solve()

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
