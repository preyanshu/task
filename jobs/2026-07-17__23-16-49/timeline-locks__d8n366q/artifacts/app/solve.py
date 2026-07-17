#!/usr/bin/env python3
import heapq
import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


COMMANDS: Tuple[str, ...] = tuple(
    sorted(
        (
            "move east",
            "move west",
            "push east",
            "take key",
            "turn clockwise",
            "turn counterclockwise",
            "use key",
            "wait",
        )
    )
)

DIR_TO_INDEX = {"N": 0, "E": 1, "S": 2, "W": 3}


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: int
    has_key: bool


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: Optional[int]
    ice: frozenset
    plate: int
    key_position: int
    goal: int
    target_dial: int


def load_level(path: str) -> Tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    start = raw["start"]
    level = Level(
        length=raw["length"],
        conveyor=raw["conveyor"],
        ice=frozenset(raw["ice"]),
        plate=raw["plate"],
        key_position=raw["key_position"],
        goal=raw["goal"],
        target_dial=DIR_TO_INDEX[raw["target_dial"]],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIR_TO_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def can_player_enter(cell: int, state: State, level: Level) -> bool:
    if not (0 <= cell < level.length):
        return False
    if cell == state.crate:
        return False
    if cell == level.key_position and state.crate != level.plate:
        return False
    return True


def apply_post_phases(
    player: int, crate: int, dial: int, level: Level
) -> Tuple[int, int]:
    wear = 0

    while crate in level.ice:
        next_crate = crate + 1
        if next_crate >= level.length or next_crate == player:
            break
        crate = next_crate
        wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if dial == DIR_TO_INDEX["E"]:
            next_crate = crate + 1
        elif dial == DIR_TO_INDEX["W"]:
            next_crate = crate - 1
        else:
            next_crate = crate

        if next_crate != crate and 0 <= next_crate < level.length and next_crate != player:
            crate = next_crate

    return crate, wear


def solve(level: Level, start: State) -> List[str]:
    start_cost = (0, 0, 0, ())
    best: Dict[State, Tuple[int, int, int, Tuple[int, ...]]] = {start: start_cost}
    heap: List[Tuple[int, int, int, Tuple[int, ...], State]] = [
        (0, 0, 0, (), start)
    ]

    while heap:
        steps, pushes, wear, transcript, state = heapq.heappop(heap)
        cost = (steps, pushes, wear, transcript)
        if best.get(state) != cost:
            continue

        for command_index, command in enumerate(COMMANDS):
            transition = step_with_wear(state, command, level)
            if transition is None:
                continue

            next_state, push_used, transition_wear, solved = transition
            updated_cost = (
                steps + 1,
                pushes + push_used,
                wear + transition_wear,
                transcript + (command_index,),
            )

            if solved:
                return [COMMANDS[index] for index in updated_cost[3]]

            previous_cost = best.get(next_state)
            if previous_cost is None or updated_cost < previous_cost:
                best[next_state] = updated_cost
                heapq.heappush(
                    heap,
                    (
                        updated_cost[0],
                        updated_cost[1],
                        updated_cost[2],
                        updated_cost[3],
                        next_state,
                    ),
                )

    raise RuntimeError("Level is unsolvable")


def step_with_wear(
    state: State, command: str, level: Level
) -> Optional[Tuple[State, int, int, bool]]:
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    solved = False
    push_used = 0

    if command == "move east":
        next_player = player + 1
        if not can_player_enter(next_player, state, level):
            return None
        player = next_player
    elif command == "move west":
        next_player = player - 1
        if not can_player_enter(next_player, state, level):
            return None
        player = next_player
    elif command == "push east":
        next_crate = crate + 1
        if player != crate - 1:
            return None
        if next_crate >= level.length:
            return None
        crate = next_crate
        push_used = 1
    elif command == "take key":
        if player != level.key_position or has_key:
            return None
        has_key = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
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
        raise ValueError(f"Unknown command: {command}")

    wear = 0
    if not solved:
        crate, wear = apply_post_phases(player, crate, dial, level)

    next_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
    return next_state, push_used, wear, solved


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        raise SystemExit("Usage: python3 /app/solve.py <level.json> <output.json>")

    level, start = load_level(argv[1])
    commands = solve(level, start)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
