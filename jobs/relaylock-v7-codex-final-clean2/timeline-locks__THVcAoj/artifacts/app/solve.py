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
COMMAND_INDEX = {command: index for index, command in enumerate(COMMANDS)}

CLOCKWISE = {"N": "E", "E": "S", "S": "W", "W": "N"}
COUNTERCLOCKWISE = {value: key for key, value in CLOCKWISE.items()}


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: str


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: str
    has_key: bool
    solved: bool = False


def move_crate(
    level: Level, player: int, crate: int, delta: int
) -> Optional[Tuple[int, int]]:
    new_crate = crate + delta
    if new_crate < 0 or new_crate >= level.length:
        return None
    if new_crate == player:
        return None
    wear = 1 if new_crate in level.ice else 0
    return new_crate, wear


def apply_slide(level: Level, player: int, crate: int) -> Optional[Tuple[int, int]]:
    wear = 0
    while crate in level.ice:
        moved = move_crate(level, player, crate, 1)
        if moved is None:
            return None
        crate, extra_wear = moved
        wear += extra_wear
    return crate, wear


def apply_conveyor(level: Level, player: int, crate: int, dial: str) -> Optional[Tuple[int, int]]:
    if level.conveyor is None or crate != level.conveyor:
        return crate, 0
    if dial == "E":
        delta = 1
    elif dial == "W":
        delta = -1
    else:
        delta = 0
    if delta == 0:
        return crate, 0
    return move_crate(level, player, crate, delta)


def transition(level: Level, state: State, command: str) -> Optional[Tuple[State, int, int]]:
    if state.solved:
        return None

    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    pushes = 0
    wear = 0
    solved = False

    if command == "move east":
        new_player = player + 1
        if new_player >= level.length or new_player == crate:
            return None
        player = new_player
    elif command == "move west":
        new_player = player - 1
        if new_player < 0 or new_player == crate:
            return None
        player = new_player
    elif command == "turn clockwise":
        dial = CLOCKWISE[dial]
    elif command == "turn counterclockwise":
        dial = COUNTERCLOCKWISE[dial]
    elif command == "push east":
        if player + 1 != crate:
            return None
        moved = move_crate(level, player, crate, 1)
        if moved is None:
            return None
        crate, extra_wear = moved
        wear += extra_wear
        pushes = 1
    elif command == "take key":
        if has_key or player != level.key_position or crate != level.plate:
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

    slid = apply_slide(level, player, crate)
    if slid is None:
        return None
    crate, extra_wear = slid
    wear += extra_wear

    conveyed = apply_conveyor(level, player, crate, dial)
    if conveyed is None:
        return None
    crate, extra_wear = conveyed
    wear += extra_wear

    return State(player, crate, dial, has_key, solved), pushes, wear


def solve(level_data: Dict[str, object]) -> List[str]:
    level = Level(
        length=int(level_data["length"]),
        conveyor=level_data.get("conveyor"),
        ice=frozenset(level_data["ice"]),
        plate=int(level_data["plate"]),
        key_position=int(level_data["key_position"]),
        goal=int(level_data["goal"]),
        target_dial=str(level_data["target_dial"]),
    )

    start_data = level_data["start"]
    start = State(
        player=int(start_data["player"]),
        crate=int(start_data["crate"]),
        dial=str(start_data["dial"]),
        has_key=bool(start_data["key"]),
        solved=False,
    )

    heap: List[Tuple[int, int, int, Tuple[int, ...], State]] = []
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {}
    start_cost = (0, 0, 0, ())
    heapq.heappush(heap, (*start_cost, start))
    best[start] = start_cost

    while heap:
        commands_used, pushes_used, wear_used, path, state = heapq.heappop(heap)
        if best.get(state) != (commands_used, pushes_used, wear_used, path):
            continue
        if state.solved:
            return [COMMANDS[index] for index in path]

        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue
            next_state, delta_pushes, delta_wear = result
            next_path = path + (COMMAND_INDEX[command],)
            next_cost = (
                commands_used + 1,
                pushes_used + delta_pushes,
                wear_used + delta_wear,
                next_path,
            )
            if next_state not in best or next_cost < best[next_state]:
                best[next_state] = next_cost
                heapq.heappush(heap, (*next_cost, next_state))

    return []


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        return 1

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as infile:
        level_data = json.load(infile)

    commands = solve(level_data)
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump({"commands": commands}, outfile, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
