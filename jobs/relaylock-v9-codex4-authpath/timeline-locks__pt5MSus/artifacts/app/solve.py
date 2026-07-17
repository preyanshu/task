#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


COMMANDS = tuple(
    sorted(
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
)

DIALS = ("N", "E", "S", "W")
TURN_CLOCKWISE = {"N": "E", "E": "S", "S": "W", "W": "N"}
TURN_COUNTERCLOCKWISE = {value: key for key, value in TURN_CLOCKWISE.items()}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


class Solver:
    def __init__(self, level: Dict[str, object]) -> None:
        self.length = int(level["length"])
        start = level["start"]
        self.start = State(
            player=int(start["player"]),
            crate=int(start["crate"]),
            dial=str(start["dial"]),
            has_key=bool(start["key"]),
        )
        conveyor = level["conveyor"]
        self.conveyor = None if conveyor is None else int(conveyor)
        self.ice = frozenset(int(value) for value in level["ice"])
        self.plate = int(level["plate"])
        self.key_position = int(level["key_position"])
        self.goal = int(level["goal"])
        self.target_dial = str(level["target_dial"])

    def in_bounds(self, position: int) -> bool:
        return 0 <= position < self.length

    def route_open(self, crate: int) -> bool:
        return crate == self.plate

    def can_player_enter(self, destination: int, crate: int) -> bool:
        if not self.in_bounds(destination):
            return False
        if destination == crate:
            return False
        if destination == self.key_position and not self.route_open(crate):
            return False
        return True

    def slide_crate(self, state: State) -> Optional[Tuple[State, int]]:
        crate = state.crate
        wear = 0
        # The spec defines a 1D device and makes sliding mandatory while on ice.
        # With no alternate slide direction specified, resolve ice as repeated eastward motion.
        while crate in self.ice:
            next_crate = crate + 1
            if not self.in_bounds(next_crate):
                return None
            if next_crate == state.player:
                return None
            crate = next_crate
            if crate in self.ice:
                wear += 1
        return State(state.player, crate, state.dial, state.has_key), wear

    def apply_conveyor(self, state: State) -> State:
        if self.conveyor is None or state.crate != self.conveyor:
            return state
        if state.dial == "E":
            destination = state.crate + 1
        elif state.dial == "W":
            destination = state.crate - 1
        else:
            return state
        if not self.in_bounds(destination) or destination == state.player:
            return state
        return State(state.player, destination, state.dial, state.has_key)

    def after_primary(self, state: State) -> Optional[Tuple[State, int]]:
        slid = self.slide_crate(state)
        if slid is None:
            return None
        slid_state, wear = slid
        return self.apply_conveyor(slid_state), wear

    def transition(self, state: State, command: str) -> Optional[Tuple[Optional[State], int, int]]:
        if command == "move east":
            destination = state.player + 1
            if not self.can_player_enter(destination, state.crate):
                return None
            primary = State(destination, state.crate, state.dial, state.has_key)
            result = self.after_primary(primary)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 0, wear

        if command == "move west":
            destination = state.player - 1
            if not self.can_player_enter(destination, state.crate):
                return None
            primary = State(destination, state.crate, state.dial, state.has_key)
            result = self.after_primary(primary)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 0, wear

        if command == "turn clockwise":
            primary = State(state.player, state.crate, TURN_CLOCKWISE[state.dial], state.has_key)
            result = self.after_primary(primary)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 0, wear

        if command == "turn counterclockwise":
            primary = State(
                state.player, state.crate, TURN_COUNTERCLOCKWISE[state.dial], state.has_key
            )
            result = self.after_primary(primary)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 0, wear

        if command == "push east":
            if state.player != state.crate - 1:
                return None
            destination = state.crate + 1
            if not self.in_bounds(destination):
                return None
            primary = State(state.player, destination, state.dial, state.has_key)
            result = self.after_primary(primary)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 1, wear

        if command == "take key":
            if state.has_key or state.player != self.key_position:
                return None
            primary = State(state.player, state.crate, state.dial, True)
            result = self.after_primary(primary)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 0, wear

        if command == "use key":
            if (
                state.player != self.goal
                or not state.has_key
                or state.crate != self.plate
                or state.dial != self.target_dial
            ):
                return None
            return None, 0, 0

        if command == "wait":
            result = self.after_primary(state)
            if result is None:
                return None
            next_state, wear = result
            return next_state, 0, wear

        raise ValueError(f"unknown command: {command}")

    def solve(self) -> List[str]:
        start_path: Tuple[int, ...] = ()
        heap: List[Tuple[Tuple[int, int, int], Tuple[int, ...], Optional[State]]] = [
            ((0, 0, 0), start_path, self.start)
        ]
        best: Dict[State, Tuple[Tuple[int, int, int], Tuple[int, ...]]] = {
            self.start: ((0, 0, 0), start_path)
        }

        while heap:
            cost_key, path_key, state = heapq.heappop(heap)
            if state is None:
                return [COMMANDS[index] for index in path_key]

            best_entry = best.get(state)
            if best_entry is None or best_entry != (cost_key, path_key):
                continue

            for command_index, command in enumerate(COMMANDS):
                transition = self.transition(state, command)
                if transition is None:
                    continue
                next_state, push_delta, wear_delta = transition
                next_cost = (
                    cost_key[0] + 1,
                    cost_key[1] + push_delta,
                    cost_key[2] + wear_delta,
                )
                next_path = path_key + (command_index,)

                if next_state is None:
                    heapq.heappush(heap, (next_cost, next_path, None))
                    continue

                previous = best.get(next_state)
                if previous is not None and previous <= (next_cost, next_path):
                    continue
                best[next_state] = (next_cost, next_path)
                heapq.heappush(heap, (next_cost, next_path, next_state))

        return []


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as handle:
        level = json.load(handle)

    commands = Solver(level).solve()

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
