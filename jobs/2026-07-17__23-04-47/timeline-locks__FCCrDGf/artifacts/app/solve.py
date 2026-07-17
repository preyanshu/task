#!/usr/bin/env python3
import json
import heapq
import sys
from typing import Dict, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: idx for idx, dial in enumerate(DIALS)}

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
QueueEntry = Tuple[int, int, int, Tuple[int, ...], State]


class Solver:
    def __init__(self, level: Dict[str, object]) -> None:
        self.length = int(level["length"])
        start = level["start"]
        if not isinstance(start, dict):
            raise ValueError("start must be an object")
        self.initial_state: State = (
            int(start["player"]),
            int(start["crate"]),
            DIAL_INDEX[str(start["dial"])],
            bool(start["key"]),
        )
        conveyor = level["conveyor"]
        self.conveyor: Optional[int] = None if conveyor is None else int(conveyor)
        self.ice = frozenset(int(pos) for pos in level["ice"])
        self.plate = int(level["plate"])
        self.key_position = int(level["key_position"])
        self.goal = int(level["goal"])
        self.target_dial = DIAL_INDEX[str(level["target_dial"])]

    def can_enter(self, destination: int, crate: int) -> bool:
        if not (0 <= destination < self.length):
            return False
        if destination == crate:
            return False
        if destination == self.key_position and crate != self.plate:
            return False
        return True

    def slide_crate(self, player: int, crate: int) -> Tuple[int, int]:
        wear = 0
        while crate in self.ice:
            next_crate = crate + 1
            if next_crate >= self.length or next_crate == player:
                break
            crate = next_crate
            wear += 1
        return crate, wear

    def apply(self, state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
        player, crate, dial, has_key = state
        push_cost = 0

        if command == "move east":
            next_player = player + 1
            if not self.can_enter(next_player, crate):
                return None
            player = next_player
        elif command == "move west":
            next_player = player - 1
            if not self.can_enter(next_player, crate):
                return None
            player = next_player
        elif command == "push east":
            next_crate = crate + 1
            if player != crate - 1 or next_crate >= self.length:
                return None
            crate = next_crate
            push_cost = 1
        elif command == "take key":
            if player != self.key_position or has_key:
                return None
            has_key = True
        elif command == "turn clockwise":
            dial = (dial + 1) % 4
        elif command == "turn counterclockwise":
            dial = (dial - 1) % 4
        elif command == "use key":
            if not (
                player == self.goal
                and has_key
                and crate == self.plate
                and dial == self.target_dial
            ):
                return None
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        crate, wear = self.slide_crate(player, crate)

        if self.conveyor is not None and crate == self.conveyor and dial in (1, 3):
            delta = 1 if dial == 1 else -1
            next_crate = crate + delta
            if 0 <= next_crate < self.length and next_crate != player:
                crate = next_crate

        solved = (
            command == "use key"
            and player == self.goal
            and has_key
            and crate == self.plate
            and dial == self.target_dial
        )
        return (player, crate, dial, has_key), push_cost, wear, solved

    def solve(self) -> List[str]:
        start_path: Tuple[int, ...] = ()
        start_entry: QueueEntry = (0, 0, 0, start_path, self.initial_state)
        heap: List[QueueEntry] = [start_entry]
        best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {
            self.initial_state: (0, 0, 0, start_path)
        }

        while heap:
            steps, pushes, wear, path, state = heapq.heappop(heap)
            if best.get(state) != (steps, pushes, wear, path):
                continue

            for command_index, command in enumerate(COMMANDS):
                result = self.apply(state, command)
                if result is None:
                    continue

                next_state, push_cost, wear_cost, solved = result
                next_path = path + (command_index,)
                next_key = (
                    steps + 1,
                    pushes + push_cost,
                    wear + wear_cost,
                    next_path,
                )

                if solved:
                    return [COMMANDS[idx] for idx in next_path]

                prev_best = best.get(next_state)
                if prev_best is None or next_key < prev_best:
                    best[next_state] = next_key
                    heapq.heappush(
                        heap,
                        (next_key[0], next_key[1], next_key[2], next_key[3], next_state),
                    )

        raise RuntimeError("level has no solution")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 /app/solve.py <level.json> <output.json>", file=sys.stderr)
        return 2

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level = json.load(infile)

    commands = Solver(level).solve()

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
