#!/usr/bin/env python3
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
INT_TO_DIAL = ["N", "E", "S", "W"]


def better_label(candidate, incumbent):
    return candidate < incumbent


class RelayLockSolver:
    def __init__(self, level):
        self.length = level["length"]
        start = level["start"]
        self.start_state = (
            start["player"],
            start["crate"],
            DIAL_TO_INT[start["dial"]],
            bool(start["key"]),
        )
        self.conveyor = level["conveyor"]
        self.ice = frozenset(level["ice"])
        self.plate = level["plate"]
        self.key_position = level["key_position"]
        self.goal = level["goal"]
        self.target_dial = DIAL_TO_INT[level["target_dial"]]

    def in_bounds(self, pos):
        return 0 <= pos < self.length

    def route_open(self, crate_pos):
        return crate_pos == self.plate

    def can_enter(self, dest, crate_pos):
        if dest == crate_pos:
            return False
        if dest == self.key_position and not self.route_open(crate_pos):
            return False
        return self.in_bounds(dest)

    def run_post_phases(self, player, crate, dial):
        wear = 0

        while crate in self.ice:
            nxt = crate + 1
            if not self.in_bounds(nxt) or nxt == player:
                break
            crate = nxt
            wear += 1

        if self.conveyor is not None and crate == self.conveyor and dial in (1, 3):
            delta = 1 if dial == 1 else -1
            nxt = crate + delta
            if self.in_bounds(nxt) and nxt != player:
                crate = nxt

        return crate, wear

    def is_use_key_legal(self, player, crate, dial, has_key):
        return (
            player == self.goal
            and has_key
            and crate == self.plate
            and dial == self.target_dial
        )

    def is_solved_after_use(self, player, crate, dial, has_key):
        return (
            player == self.goal
            and has_key
            and crate == self.plate
            and dial == self.target_dial
        )

    def apply(self, state, command):
        player, crate, dial, has_key = state
        push_cost = 0

        if command == "move east":
            dest = player + 1
            if not self.can_enter(dest, crate):
                return None
            player = dest
        elif command == "move west":
            dest = player - 1
            if not self.can_enter(dest, crate):
                return None
            player = dest
        elif command == "turn clockwise":
            dial = (dial + 1) % 4
        elif command == "turn counterclockwise":
            dial = (dial - 1) % 4
        elif command == "push east":
            if player + 1 != crate:
                return None
            nxt = crate + 1
            if not self.in_bounds(nxt):
                return None
            crate = nxt
            push_cost = 1
        elif command == "take key":
            if player != self.key_position or has_key:
                return None
            has_key = True
        elif command == "use key":
            if not self.is_use_key_legal(player, crate, dial, has_key):
                return None
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        crate, wear_cost = self.run_post_phases(player, crate, dial)
        next_state = (player, crate, dial, has_key)
        solved = command == "use key" and self.is_solved_after_use(
            player, crate, dial, has_key
        )
        return next_state, push_cost, wear_cost, solved

    def solve(self):
        start = self.start_state
        frontier = {start: (0, 0, ())}
        seen_depth = {start: 0}
        depth = 0

        while frontier:
            next_frontier = {}
            solutions = []

            for state, label in frontier.items():
                pushes, wear, path = label

                for index, command in enumerate(COMMANDS):
                    outcome = self.apply(state, command)
                    if outcome is None:
                        continue

                    next_state, push_delta, wear_delta, solved = outcome
                    next_label = (
                        pushes + push_delta,
                        wear + wear_delta,
                        path + (index,),
                    )

                    if solved:
                        solutions.append(next_label)
                        continue

                    next_depth = depth + 1
                    previous_depth = seen_depth.get(next_state)
                    if previous_depth is None:
                        seen_depth[next_state] = next_depth
                        next_frontier[next_state] = next_label
                    elif previous_depth == next_depth:
                        current = next_frontier[next_state]
                        if better_label(next_label, current):
                            next_frontier[next_state] = next_label

            if solutions:
                best = min(solutions)
                return [COMMANDS[i] for i in best[2]]

            frontier = next_frontier
            depth += 1

        raise RuntimeError("level is unsolvable")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as f:
        level = json.load(f)

    commands = RelayLockSolver(level).solve()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"commands": commands}, f, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
