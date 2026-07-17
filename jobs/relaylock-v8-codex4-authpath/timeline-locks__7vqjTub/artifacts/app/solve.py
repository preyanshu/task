#!/usr/bin/env python3
import json
import sys
from dataclasses import dataclass


DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}
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


@dataclass(frozen=True)
class Level:
    length: int
    conveyor: int | None
    ice: frozenset[int]
    plate: int
    key_position: int
    goal: int
    target_dial: int


@dataclass(frozen=True)
class State:
    player: int
    crate: int
    dial: int
    has_key: bool


def load_level(path: str) -> tuple[Level, State]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    start = data["start"]
    level = Level(
        length=data["length"],
        conveyor=data["conveyor"],
        ice=frozenset(data["ice"]),
        plate=data["plate"],
        key_position=data["key_position"],
        goal=data["goal"],
        target_dial=DIAL_INDEX[data["target_dial"]],
    )
    state = State(
        player=start["player"],
        crate=start["crate"],
        dial=DIAL_INDEX[start["dial"]],
        has_key=bool(start["key"]),
    )
    return level, state


def slide_and_convey(level: Level, player: int, crate: int, dial: int) -> tuple[int, int]:
    wear = 0

    while crate in level.ice:
        next_crate = crate + 1
        if next_crate >= level.length:
            break
        crate = next_crate
        if crate in level.ice:
            wear += 1

    if level.conveyor is not None and crate == level.conveyor:
        if dial == DIAL_INDEX["E"]:
            next_crate = crate + 1
        elif dial == DIAL_INDEX["W"]:
            next_crate = crate - 1
        else:
            next_crate = None
        if next_crate is not None and 0 <= next_crate < level.length and next_crate != player:
            crate = next_crate

    return crate, wear


def simulate(level: Level, state: State, command: str):
    player = state.player
    crate = state.crate
    dial = state.dial
    has_key = state.has_key
    push_cost = 0

    route_open = crate == level.plate

    if command == "move east":
        destination = player + 1
        if destination >= level.length or destination == crate:
            return None
        if destination == level.key_position and not route_open:
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if destination < 0 or destination == crate:
            return None
        if destination == level.key_position and not route_open:
            return None
        player = destination
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        if player + 1 != crate or crate + 1 >= level.length:
            return None
        crate += 1
        push_cost = 1
    elif command == "take key":
        if has_key or player != level.key_position:
            return None
        has_key = True
    elif command == "use key":
        if (
            player == level.goal
            and has_key
            and crate == level.plate
            and dial == level.target_dial
        ):
            return ("solved", 0, 0)
        return None
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    crate, wear = slide_and_convey(level, player, crate, dial)
    next_state = State(player=player, crate=crate, dial=dial, has_key=has_key)
    return (next_state, push_cost, wear)


def solve(level: Level, start: State) -> list[str]:
    frontier: dict[State, tuple[int, int, tuple[int, ...]]] = {
        start: (0, 0, ())
    }
    seen_depth = {start: 0}
    depth = 0

    while frontier:
        next_frontier: dict[State, tuple[int, int, tuple[int, ...]]] = {}
        best_solution: tuple[int, int, tuple[int, ...]] | None = None

        for state, label in sorted(frontier.items(), key=lambda item: item[1][2]):
            pushes, wear, path = label
            for index, command in enumerate(COMMANDS):
                outcome = simulate(level, state, command)
                if outcome is None:
                    continue

                candidate = (pushes + outcome[1], wear + outcome[2], path + (index,))
                if outcome[0] == "solved":
                    if best_solution is None or candidate < best_solution:
                        best_solution = candidate
                    continue

                next_state = outcome[0]
                prior_depth = seen_depth.get(next_state)
                if prior_depth is not None and prior_depth < depth + 1:
                    continue
                current_best = next_frontier.get(next_state)
                if current_best is None or candidate < current_best:
                    next_frontier[next_state] = candidate

        if best_solution is not None:
            return [COMMANDS[index] for index in best_solution[2]]

        depth += 1
        for state in next_frontier:
            seen_depth[state] = depth
        frontier = next_frontier

    raise RuntimeError("level is unsolved")


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level, start = load_level(sys.argv[1])
    commands = solve(level, start)

    with open(sys.argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
