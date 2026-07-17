#!/usr/bin/env python3

import heapq
import json
import sys
from dataclasses import dataclass


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


DIAL_CLOCKWISE = {
    "N": "E",
    "E": "S",
    "S": "W",
    "W": "N",
}


DIAL_COUNTERCLOCKWISE = {value: key for key, value in DIAL_CLOCKWISE.items()}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


class Level:
    def __init__(self, raw):
        self.length = raw["length"]
        start = raw["start"]
        self.start_state = State(
            player=start["player"],
            crate=start["crate"],
            dial=start["dial"],
            has_key=bool(start["key"]),
        )
        self.conveyor = raw["conveyor"]
        self.ice = set(raw["ice"])
        self.plate = raw["plate"]
        self.key_position = raw["key_position"]
        self.goal = raw["goal"]
        self.target_dial = raw["target_dial"]

    def in_bounds(self, position):
        return 0 <= position < self.length

    def route_open(self, state):
        return state.crate == self.plate

    def can_enter(self, state, position):
        if not self.in_bounds(position):
            return False
        if position == state.crate:
            return False
        if position == self.key_position and not self.route_open(state):
            return False
        return True

    def apply_post_command(self, player, crate, dial, has_key):
        wear = 0

        while crate in self.ice:
            next_crate = crate + 1
            if not self.in_bounds(next_crate) or next_crate == player:
                break
            crate = next_crate
            wear += 1

        if crate == self.conveyor and dial in ("E", "W"):
            delta = 1 if dial == "E" else -1
            next_crate = crate + delta
            if self.in_bounds(next_crate) and next_crate != player:
                crate = next_crate

        return State(player=player, crate=crate, dial=dial, has_key=has_key), wear

    def transition(self, state, command):
        player = state.player
        crate = state.crate
        dial = state.dial
        has_key = state.has_key
        push_cost = 0
        solved = False

        if command == "move east":
            next_player = player + 1
            if not self.can_enter(state, next_player):
                return None
            player = next_player
        elif command == "move west":
            next_player = player - 1
            if not self.can_enter(state, next_player):
                return None
            player = next_player
        elif command == "turn clockwise":
            dial = DIAL_CLOCKWISE[dial]
        elif command == "turn counterclockwise":
            dial = DIAL_COUNTERCLOCKWISE[dial]
        elif command == "push east":
            if player + 1 != crate:
                return None
            next_crate = crate + 1
            if not self.in_bounds(next_crate):
                return None
            crate = next_crate
            push_cost = 1
        elif command == "take key":
            if player != self.key_position or has_key:
                return None
            has_key = True
        elif command == "use key":
            if (
                player != self.goal
                or not has_key
                or crate != self.plate
                or dial != self.target_dial
            ):
                return None
            solved = True
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        next_state, wear = self.apply_post_command(player, crate, dial, has_key)
        return next_state, push_cost, wear, solved


def solve(level):
    start = level.start_state
    start_cost = (0, 0, 0, ())
    best_cost = {start: start_cost}
    heap = [start_cost + (0, start)]

    while heap:
        steps, pushes, wear, path, solved_flag, state = heapq.heappop(heap)
        if solved_flag:
            return list(path)

        cost = (steps, pushes, wear, path)
        if best_cost.get(state) != cost:
            continue

        for command in COMMANDS:
            result = level.transition(state, command)
            if result is None:
                continue
            next_state, push_cost, wear_cost, solved = result
            next_path = path + (command,)
            next_cost = (
                steps + 1,
                pushes + push_cost,
                wear + wear_cost,
                next_path,
            )
            if solved:
                heapq.heappush(heap, next_cost + (1, None))
                continue
            previous = best_cost.get(next_state)
            if previous is None or next_cost < previous:
                best_cost[next_state] = next_cost
                heapq.heappush(heap, next_cost + (0, next_state))

    raise ValueError("level is unsolvable")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = solve(Level(level_data))

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
