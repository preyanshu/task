#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


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

DIALS = "NESW"
CW = {"N": "E", "E": "S", "S": "W", "W": "N"}
CCW = {v: k for k, v in CW.items()}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool
    solved: bool = False


@dataclass(frozen=True)
class Step:
    state: State
    pushes: int
    wear: int


class Level:
    def __init__(self, data: Dict[str, object]) -> None:
        self.length = int(data["length"])
        start = data["start"]
        self.start = State(
            player=int(start["player"]),
            crate=int(start["crate"]),
            dial=str(start["dial"]),
            has_key=bool(start["key"]),
        )
        self.conveyor = data["conveyor"]
        if self.conveyor is not None:
            self.conveyor = int(self.conveyor)
        self.ice = frozenset(int(pos) for pos in data["ice"])
        self.plate = int(data["plate"])
        self.key_position = int(data["key_position"])
        self.goal = int(data["goal"])
        self.target_dial = str(data["target_dial"])

    def in_bounds(self, pos: int) -> bool:
        return 0 <= pos < self.length

    def key_route_open(self, state: State) -> bool:
        return state.crate == self.plate

    def can_player_enter(self, state: State, pos: int) -> bool:
        if not self.in_bounds(pos) or pos == state.crate:
            return False
        if pos == self.key_position and not state.has_key and not self.key_route_open(state):
            return False
        return True

    def can_crate_enter(self, player: int, pos: int) -> bool:
        return self.in_bounds(pos) and pos != player

    def slide_crate(self, player: int, crate: int) -> Tuple[int, int]:
        wear = 0
        while crate in self.ice:
            nxt = crate + 1
            if not self.can_crate_enter(player, nxt):
                break
            crate = nxt
            if crate in self.ice:
                wear += 1
        return crate, wear

    def conveyor_move(self, player: int, crate: int, dial: str) -> Tuple[int, int]:
        if crate != self.conveyor:
            return crate, 0
        delta = 1 if dial == "E" else -1 if dial == "W" else 0
        if delta == 0:
            return crate, 0
        nxt = crate + delta
        if not self.can_crate_enter(player, nxt):
            return crate, 0
        return nxt, 1 if nxt in self.ice else 0

    def transition(self, state: State, command: str) -> Optional[Step]:
        player = state.player
        crate = state.crate
        dial = state.dial
        has_key = state.has_key
        pushes = 0
        wear = 0

        if command == "move east":
            nxt = player + 1
            if not self.can_player_enter(state, nxt):
                return None
            player = nxt
        elif command == "move west":
            nxt = player - 1
            if not self.can_player_enter(state, nxt):
                return None
            player = nxt
        elif command == "turn clockwise":
            dial = CW[dial]
        elif command == "turn counterclockwise":
            dial = CCW[dial]
        elif command == "push east":
            if player + 1 != crate:
                return None
            nxt = crate + 1
            if not self.can_crate_enter(player, nxt):
                return None
            crate = nxt
            pushes = 1
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
            return Step(
                state=State(
                    player=player,
                    crate=crate,
                    dial=dial,
                    has_key=has_key,
                    solved=True,
                ),
                pushes=pushes,
                wear=wear,
            )
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        crate, extra_wear = self.slide_crate(player, crate)
        wear += extra_wear
        crate, extra_wear = self.conveyor_move(player, crate, dial)
        wear += extra_wear

        return Step(
            state=State(player=player, crate=crate, dial=dial, has_key=has_key),
            pushes=pushes,
            wear=wear,
        )


def solve(level: Level) -> List[str]:
    start = level.start
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {}
    heap: List[Tuple[int, int, int, Tuple[int, ...], State]] = []
    start_cost = (0, 0, 0, ())
    best[start] = start_cost
    heapq.heappush(heap, (0, 0, 0, (), start))

    while heap:
        steps, pushes, wear, path, state = heapq.heappop(heap)
        if best.get(state) != (steps, pushes, wear, path):
            continue
        if state.solved:
            return [COMMANDS[i] for i in path]

        for index, command in enumerate(COMMANDS):
            step = level.transition(state, command)
            if step is None:
                continue

            next_path = path + (index,)
            next_cost = (
                steps + 1,
                pushes + step.pushes,
                wear + step.wear,
                next_path,
            )
            current = best.get(step.state)
            if current is None or next_cost < current:
                best[step.state] = next_cost
                heapq.heappush(
                    heap,
                    (
                        next_cost[0],
                        next_cost[1],
                        next_cost[2],
                        next_cost[3],
                        step.state,
                    ),
                )

    raise ValueError("level is unsolvable")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python3 /app/solve.py <level.json> <output.json>", file=sys.stderr)
        return 1

    with open(sys.argv[1], "r", encoding="utf-8") as infile:
        level_data = json.load(infile)
    level = Level(level_data)
    commands = solve(level)
    with open(sys.argv[2], "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
