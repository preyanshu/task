#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


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
COMMAND_INDEX = {name: i for i, name in enumerate(COMMANDS)}
CW_DIAL = {"N": "E", "E": "S", "S": "W", "W": "N"}
CCW_DIAL = {value: key for key, value in CW_DIAL.items()}
CONVEYOR_DELTA = {"E": 1, "W": -1, "N": 0, "S": 0}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


class Level:
    def __init__(self, raw: Dict[str, object]) -> None:
        self.length = int(raw["length"])
        start = raw["start"]
        if not isinstance(start, dict):
            raise ValueError("start must be an object")
        self.start = State(
            player=int(start["player"]),
            crate=int(start["crate"]),
            dial=str(start["dial"]),
            has_key=bool(start["key"]),
        )
        self.conveyor = raw.get("conveyor")
        self.conveyor = None if self.conveyor is None else int(self.conveyor)
        self.ice = frozenset(int(x) for x in raw.get("ice", []))
        self.plate = int(raw["plate"])
        self.key_position = int(raw["key_position"])
        self.goal = int(raw["goal"])
        self.target_dial = str(raw["target_dial"])

    def in_bounds(self, pos: int) -> bool:
        return 0 <= pos < self.length

    def route_open(self, state: State) -> bool:
        return state.crate == self.plate


def move_crate(
    level: Level,
    player: int,
    crate: int,
    delta: int,
    wear: int,
) -> Optional[Tuple[int, int]]:
    new_crate = crate + delta
    if not level.in_bounds(new_crate) or new_crate == player:
        return None
    if new_crate in level.ice:
        wear += 1
    return new_crate, wear


def apply_sliding(level: Level, player: int, crate: int, wear: int) -> Optional[Tuple[int, int]]:
    while crate in level.ice:
        moved = move_crate(level, player, crate, 1, wear)
        if moved is None:
            return None
        crate, wear = moved
    return crate, wear


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    wear = 0
    solved = False
    pending_take = False
    pending_use = False

    if command == "move east":
        target = player + 1
        if not level.in_bounds(target) or target == crate:
            return None
        player = target
    elif command == "move west":
        target = player - 1
        if not level.in_bounds(target) or target == crate:
            return None
        player = target
    elif command == "turn clockwise":
        dial = CW_DIAL[dial]
    elif command == "turn counterclockwise":
        dial = CCW_DIAL[dial]
    elif command == "push east":
        if player != crate - 1:
            return None
        moved = move_crate(level, player, crate, 1, wear)
        if moved is None:
            return None
        crate, wear = moved
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        pending_take = True
    elif command == "use key":
        if player != level.goal or not has_key:
            return None
        pending_use = True
    elif command == "wait":
        pass
    else:
        return None

    slidden = apply_sliding(level, player, crate, wear)
    if slidden is None:
        return None
    crate, wear = slidden

    if level.conveyor is not None and crate == level.conveyor:
        delta = CONVEYOR_DELTA[dial]
        if delta:
            moved = move_crate(level, player, crate, delta, wear)
            if moved is None:
                return None
            crate, wear = moved

    if pending_take:
        candidate_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
        if not level.route_open(candidate_state):
            return None
        has_key = True

    next_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
    if pending_use:
        solved = (
            next_state.player == level.goal
            and next_state.has_key
            and next_state.crate == level.plate
            and next_state.dial == level.target_dial
        )
        if not solved:
            return None
    return next_state, wear, solved


def solve(level: Level) -> List[str]:
    start = level.start
    start_key = (0, 0, 0, ())
    heap: List[Tuple[int, int, int, Tuple[int, ...], State]] = [
        (0, 0, 0, (), start)
    ]
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_key}

    while heap:
        steps, pushes, wear, transcript, state = heapq.heappop(heap)
        current_key = (steps, pushes, wear, transcript)
        if best.get(state) != current_key:
            continue

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue
            next_state, added_wear, solved = result
            next_transcript = transcript + (COMMAND_INDEX[command],)
            next_key = (
                steps + 1,
                pushes + (1 if command == "push east" else 0),
                wear + added_wear,
                next_transcript,
            )
            prev_best = best.get(next_state)
            if prev_best is None or next_key < prev_best:
                best[next_state] = next_key
                heapq.heappush(heap, (*next_key, next_state))
            if solved:
                return [COMMANDS[i] for i in next_transcript]

    raise ValueError("Level is unsolvable")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python3 solve.py <level.json> <output.json>", file=sys.stderr)
        return 2

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        raw = json.load(infile)
    level = Level(raw)
    commands = solve(level)

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
