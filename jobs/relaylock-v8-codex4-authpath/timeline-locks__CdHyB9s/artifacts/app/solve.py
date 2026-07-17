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
CW_DIAL = {"N": "E", "E": "S", "S": "W", "W": "N"}
CCW_DIAL = {"N": "W", "W": "S", "S": "E", "E": "N"}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool


@dataclass(frozen=True)
class Transition:
    state: Optional[State]
    pushes: int
    wear: int
    solved: bool


class Level:
    def __init__(self, raw: Dict[str, object]) -> None:
        self.length = int(raw["length"])
        start = raw["start"]
        self.initial_state = State(
            player=int(start["player"]),
            crate=int(start["crate"]),
            dial=str(start["dial"]),
            has_key=bool(start["key"]),
        )
        self.conveyor = raw["conveyor"]
        self.ice = frozenset(int(pos) for pos in raw["ice"])
        self.plate = int(raw["plate"])
        self.key_position = int(raw["key_position"])
        self.goal = int(raw["goal"])
        self.target_dial = str(raw["target_dial"])

    def route_open(self, crate: int) -> bool:
        return crate == self.plate

    def in_bounds(self, pos: int) -> bool:
        return 0 <= pos < self.length


def apply_command(level: Level, state: State, command: str) -> Optional[Transition]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    solved = False
    pushes = 0
    wear = 0

    route_open = level.route_open(crate)

    if command == "move east":
        dest = player + 1
        if not level.in_bounds(dest) or dest == crate:
            return None
        if dest == level.key_position and not route_open:
            return None
        player = dest
    elif command == "move west":
        dest = player - 1
        if not level.in_bounds(dest) or dest == crate:
            return None
        if dest == level.key_position and not route_open:
            return None
        player = dest
    elif command == "turn clockwise":
        dial = CW_DIAL[dial]
    elif command == "turn counterclockwise":
        dial = CCW_DIAL[dial]
    elif command == "push east":
        if player + 1 != crate:
            return None
        dest = crate + 1
        if not level.in_bounds(dest) or dest == player:
            return None
        crate = dest
        pushes = 1
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        has_key = True
    elif command == "use key":
        if (
            player != level.goal
            or not has_key
            or crate != level.plate
            or dial != level.target_dial
        ):
            return None
        solved = True
    elif command == "wait":
        pass
    else:
        return None

    crate, wear = resolve_sliding(level, player, crate)
    crate = resolve_conveyor(level, player, crate, dial)

    if solved:
        return Transition(state=None, pushes=pushes, wear=wear, solved=True)

    return Transition(
        state=State(player=player, crate=crate, dial=dial, has_key=has_key),
        pushes=pushes,
        wear=wear,
        solved=False,
    )


def resolve_sliding(level: Level, player: int, crate: int) -> Tuple[int, int]:
    wear = 0
    while crate in level.ice:
        dest = crate + 1
        if not level.in_bounds(dest) or dest == player:
            break
        crate = dest
        if crate in level.ice:
            wear += 1
    return crate, wear


def resolve_conveyor(level: Level, player: int, crate: int, dial: str) -> int:
    if level.conveyor is None or crate != level.conveyor:
        return crate
    if dial == "E":
        dest = crate + 1
    elif dial == "W":
        dest = crate - 1
    else:
        return crate
    if not level.in_bounds(dest) or dest == player:
        return crate
    return dest


def solve(level: Level) -> List[str]:
    start = level.initial_state
    start_score = (0, 0, 0, ())
    best: Dict[State, Tuple[int, int, int, Tuple[str, ...]]] = {start: start_score}
    queue: List[Tuple[int, int, int, Tuple[str, ...], Optional[State]]] = [
        (0, 0, 0, (), start)
    ]

    while queue:
        steps, pushes, wear, transcript, state = heapq.heappop(queue)
        if state is None:
            return list(transcript)

        score = (steps, pushes, wear, transcript)
        if best.get(state) != score:
            continue

        for command in COMMANDS:
            result = apply_command(level, state, command)
            if result is None:
                continue

            next_transcript = transcript + (command,)
            next_score = (
                steps + 1,
                pushes + result.pushes,
                wear + result.wear,
                next_transcript,
            )

            if result.solved:
                heapq.heappush(
                    queue,
                    (
                        next_score[0],
                        next_score[1],
                        next_score[2],
                        next_score[3],
                        None,
                    ),
                )
                continue

            assert result.state is not None
            prev_best = best.get(result.state)
            if prev_best is None or next_score < prev_best:
                best[result.state] = next_score
                heapq.heappush(
                    queue,
                    (
                        next_score[0],
                        next_score[1],
                        next_score[2],
                        next_score[3],
                        result.state,
                    ),
                )

    raise ValueError("No solution found")


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        raw_level = json.load(infile)

    commands = solve(Level(raw_level))

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
