#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


DIALS = ("N", "E", "S", "W")
CLOCKWISE = {dial: DIALS[(index + 1) % 4] for index, dial in enumerate(DIALS)}
COUNTERCLOCKWISE = {dial: DIALS[(index - 1) % 4] for index, dial in enumerate(DIALS)}

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


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


@dataclass(frozen=True)
class Outcome:
    state: State
    pushes: int
    wear: int
    solved: bool


class Level:
    def __init__(self, raw: Dict[str, object]) -> None:
        self.length = int(raw["length"])
        start = raw["start"]
        self.start = State(
            player=int(start["player"]),
            crate=int(start["crate"]),
            dial=str(start["dial"]),
            has_key=bool(start["key"]),
        )
        self.conveyor = raw["conveyor"]
        self.ice = frozenset(int(value) for value in raw["ice"])
        self.plate = int(raw["plate"])
        self.key_position = int(raw["key_position"])
        self.goal = int(raw["goal"])
        self.target_dial = str(raw["target_dial"])

    def in_bounds(self, position: int) -> bool:
        return 0 <= position < self.length

    def plate_open(self, crate: int) -> bool:
        return crate == self.plate

    def player_move_target(self, state: State, direction: int) -> Optional[int]:
        if direction not in (-1, 1):
            raise ValueError("direction must be -1 or 1")

        plate_open = self.plate_open(state.crate)
        if direction == 1 and plate_open and state.player == self.plate - 1:
            target = self.key_position
        elif direction == -1 and plate_open and state.player == self.key_position:
            target = self.plate - 1
        else:
            target = state.player + direction

        if not self.in_bounds(target):
            return None
        if target == state.crate:
            return None
        return target

    def move_crate(self, player: int, crate: int, delta: int) -> Optional[Tuple[int, int]]:
        new_crate = crate + delta
        if not self.in_bounds(new_crate):
            return None
        if new_crate == player:
            return None
        return player, new_crate

    def simulate(self, state: State, command: str) -> Optional[Outcome]:
        player = state.player
        crate = state.crate
        dial = state.dial
        has_key = state.has_key
        pushes = 0
        wear = 0
        used_key = False
        crate_moved = False

        if command == "move east":
            target = self.player_move_target(state, 1)
            if target is None:
                return None
            player = target
        elif command == "move west":
            target = self.player_move_target(state, -1)
            if target is None:
                return None
            player = target
        elif command == "turn clockwise":
            dial = CLOCKWISE[dial]
        elif command == "turn counterclockwise":
            dial = COUNTERCLOCKWISE[dial]
        elif command == "push east":
            if player != crate - 1:
                return None
            pushed = self.move_crate(player, crate, 1)
            if pushed is None:
                return None
            player = crate
            crate = pushed[1]
            pushes = 1
            crate_moved = True
            if crate in self.ice:
                wear += 1
        elif command == "take key":
            if has_key or player != self.key_position:
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
            used_key = True
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        if crate_moved:
            while crate in self.ice:
                slid = self.move_crate(player, crate, 1)
                if slid is None:
                    return None
                crate = slid[1]
                if crate in self.ice:
                    wear += 1

        if self.conveyor is not None and crate == self.conveyor:
            delta = 0
            if dial == "E":
                delta = 1
            elif dial == "W":
                delta = -1
            if delta:
                conveyed = self.move_crate(player, crate, delta)
                if conveyed is None:
                    return None
                crate = conveyed[1]
                if crate in self.ice:
                    wear += 1

        solved = (
            used_key
            and player == self.goal
            and has_key
            and crate == self.plate
            and dial == self.target_dial
        )
        return Outcome(State(player=player, crate=crate, dial=dial, has_key=has_key), pushes, wear, solved)


def solve(level: Level) -> List[str]:
    start = level.start
    frontier: List[Tuple[int, int, int, Tuple[str, ...], State]] = []
    heapq.heappush(frontier, (0, 0, 0, (), start))
    best: Dict[State, Tuple[int, int, int, Tuple[str, ...]]] = {start: (0, 0, 0, ())}

    while frontier:
        commands_used, pushes_used, wear_used, path, state = heapq.heappop(frontier)
        if best.get(state) != (commands_used, pushes_used, wear_used, path):
            continue

        for command in COMMANDS:
            outcome = level.simulate(state, command)
            if outcome is None:
                continue

            next_path = path + (command,)
            next_cost = (
                commands_used + 1,
                pushes_used + outcome.pushes,
                wear_used + outcome.wear,
                next_path,
            )
            if outcome.solved:
                return list(next_path)

            best_cost = best.get(outcome.state)
            if best_cost is not None and best_cost <= next_cost:
                continue

            best[outcome.state] = next_cost
            heapq.heappush(
                frontier,
                (next_cost[0], next_cost[1], next_cost[2], next_cost[3], outcome.state),
            )

    raise RuntimeError("no solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 /app/solve.py <level.json> <output.json>", file=sys.stderr)
        return 2

    with open(argv[1], "r", encoding="utf-8") as infile:
        raw_level = json.load(infile)

    level = Level(raw_level)
    commands = solve(level)

    with open(argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
