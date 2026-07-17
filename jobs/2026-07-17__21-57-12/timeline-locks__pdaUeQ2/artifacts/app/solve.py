#!/usr/bin/env python3
import json
import sys
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

DIAL_TO_INDEX = {"N": 0, "E": 1, "S": 2, "W": 3}
INDEX_TO_DIAL = "NESW"
STATE = Tuple[int, int, int, bool]


class Solver:
    def __init__(self, level: Dict[str, object]) -> None:
        start = level["start"]
        self.length = int(level["length"])
        self.initial_state: STATE = (
            int(start["player"]),
            int(start["crate"]),
            DIAL_TO_INDEX[start["dial"]],
            bool(start["key"]),
        )
        self.conveyor = level["conveyor"]
        self.ice = frozenset(int(pos) for pos in level["ice"])
        self.plate = int(level["plate"])
        self.key_position = int(level["key_position"])
        self.goal = int(level["goal"])
        self.target_dial = DIAL_TO_INDEX[level["target_dial"]]

    def _route_open(self, crate: int) -> bool:
        return crate == self.plate

    def _can_player_enter(self, pos: int, crate: int) -> bool:
        if pos < 0 or pos >= self.length:
            return False
        if pos == crate:
            return False
        if pos == self.key_position and not self._route_open(crate):
            return False
        return True

    def _apply_sliding(self, player: int, crate: int) -> Tuple[int, int]:
        wear = 0
        while crate in self.ice:
            nxt = crate + 1
            if nxt < 0 or nxt >= self.length or nxt == player:
                break
            crate = nxt
            if crate in self.ice:
                wear += 1
        return crate, wear

    def _apply_conveyor(self, player: int, crate: int, dial: int) -> int:
        if self.conveyor is None or crate != self.conveyor:
            return crate
        if dial == DIAL_TO_INDEX["E"]:
            nxt = crate + 1
        elif dial == DIAL_TO_INDEX["W"]:
            nxt = crate - 1
        else:
            return crate
        if 0 <= nxt < self.length and nxt != player:
            return nxt
        return crate

    def step(self, state: STATE, command: str) -> Optional[Tuple[STATE, int, int, bool]]:
        player, crate, dial, has_key = state
        push_cost = 0
        use_key_requested = False

        if command == "move east":
            nxt = player + 1
            if not self._can_player_enter(nxt, crate):
                return None
            player = nxt
        elif command == "move west":
            nxt = player - 1
            if not self._can_player_enter(nxt, crate):
                return None
            player = nxt
        elif command == "turn clockwise":
            dial = (dial + 1) % 4
        elif command == "turn counterclockwise":
            dial = (dial - 1) % 4
        elif command == "push east":
            if player != crate - 1:
                return None
            nxt = crate + 1
            if nxt < 0 or nxt >= self.length:
                return None
            crate = nxt
            push_cost = 1
        elif command == "take key":
            if player != self.key_position:
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
            use_key_requested = True
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        crate, wear_cost = self._apply_sliding(player, crate)
        crate = self._apply_conveyor(player, crate, dial)

        solved = use_key_requested and crate == self.plate and dial == self.target_dial
        return (player, crate, dial, has_key), push_cost, wear_cost, solved

    def solve(self) -> Iterable[str]:
        frontier: Dict[STATE, Tuple[int, int, bytes]] = {self.initial_state: (0, 0, b"")}
        best_depth: Dict[STATE, int] = {self.initial_state: 0}
        depth = 0

        while frontier:
            next_frontier: Dict[STATE, Tuple[int, int, bytes]] = {}
            best_solution: Optional[Tuple[int, int, bytes]] = None

            for state, (pushes, wear, seq) in frontier.items():
                for command_index, command in enumerate(COMMANDS):
                    outcome = self.step(state, command)
                    if outcome is None:
                        continue

                    next_state, push_delta, wear_delta, solved = outcome
                    next_pushes = pushes + push_delta
                    next_wear = wear + wear_delta
                    next_seq = seq + bytes((command_index,))
                    metric = (next_pushes, next_wear, next_seq)

                    if solved:
                        if best_solution is None or metric < best_solution:
                            best_solution = metric
                        continue

                    next_depth = depth + 1
                    prior_depth = best_depth.get(next_state)
                    if prior_depth is None:
                        best_depth[next_state] = next_depth
                    elif prior_depth != next_depth:
                        continue

                    incumbent = next_frontier.get(next_state)
                    if incumbent is None or metric < incumbent:
                        next_frontier[next_state] = metric

            if best_solution is not None:
                return [COMMANDS[index] for index in best_solution[2]]

            frontier = next_frontier
            depth += 1

        raise RuntimeError("no solution found")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level = json.load(infile)

    commands = list(Solver(level).solve())

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))


if __name__ == "__main__":
    main()
