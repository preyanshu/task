#!/usr/bin/env python3
import heapq
import json
import sys
from typing import Dict, Iterable, List, Optional, Tuple


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

DIALS = "NESW"
SOLVED = ("__solved__",)
State = Tuple[int, int, str, bool]
Cost = Tuple[int, int, int]
Node = Tuple[object, ...]


def turn_clockwise(dial: str) -> str:
    return DIALS[(DIALS.index(dial) + 1) % len(DIALS)]


def turn_counterclockwise(dial: str) -> str:
    return DIALS[(DIALS.index(dial) - 1) % len(DIALS)]


def load_level(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and "levels" in data:
        levels = data.get("levels")
        if isinstance(levels, list) and len(levels) == 1 and isinstance(levels[0], dict):
            return levels[0]
    if not isinstance(data, dict):
        raise ValueError("Level JSON must be an object.")
    return data


def initial_state(level: Dict[str, object]) -> State:
    start = level["start"]
    if not isinstance(start, dict):
        raise ValueError("start must be an object.")
    return (
        int(start["player"]),
        int(start["crate"]),
        str(start["dial"]),
        bool(start["key"]),
    )


def conveyor_delta(dial: str) -> int:
    if dial == "E":
        return 1
    if dial == "W":
        return -1
    return 0


def can_take_key(level: Dict[str, object], player: int, crate: int, has_key: bool) -> bool:
    # The spec states that the plate opens the route to the key.
    return (
        not has_key
        and player == int(level["key_position"])
        and crate == int(level["plate"])
    )


def can_use_key(level: Dict[str, object], state: State) -> bool:
    player, crate, dial, has_key = state
    return (
        has_key
        and player == int(level["goal"])
        and crate == int(level["plate"])
        and dial == str(level["target_dial"])
    )


def move_crate(
    level: Dict[str, object],
    crate: int,
    player: int,
    delta: int,
) -> Tuple[int, int]:
    length = int(level["length"])
    ice = level["ice"]
    if not isinstance(ice, list):
        raise ValueError("ice must be a list.")
    target = crate + delta
    if target < 0 or target >= length or target == player:
        return crate, 0
    wear = 1 if target in ice else 0
    return target, wear


def apply_command(level: Dict[str, object], state: State, command: str) -> Optional[Tuple[State, int, int, bool]]:
    length = int(level["length"])
    conveyor = level["conveyor"]
    ice = level["ice"]
    if not isinstance(ice, list):
        raise ValueError("ice must be a list.")

    player, crate, dial, has_key = state
    pushes = 0
    wear = 0

    if command == "move east":
        target = player + 1
        if target >= length or target == crate:
            return None
        player = target
    elif command == "move west":
        target = player - 1
        if target < 0 or target == crate:
            return None
        player = target
    elif command == "turn clockwise":
        dial = turn_clockwise(dial)
    elif command == "turn counterclockwise":
        dial = turn_counterclockwise(dial)
    elif command == "push east":
        if player != crate - 1 or crate + 1 >= length:
            return None
        crate, gained = move_crate(level, crate, player, 1)
        if crate == state[1]:
            return None
        wear += gained
        pushes = 1
    elif command == "take key":
        if not can_take_key(level, player, crate, has_key):
            return None
        has_key = True
    elif command == "use key":
        if not can_use_key(level, state):
            return None
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    # Ice is modeled as an eastward forced slide in the device's single travel axis.
    while crate in ice:
        next_crate, gained = move_crate(level, crate, player, 1)
        if next_crate == crate:
            break
        crate = next_crate
        wear += gained

    if conveyor is not None and crate == int(conveyor):
        delta = conveyor_delta(dial)
        if delta:
            crate, gained = move_crate(level, crate, player, delta)
            wear += gained

    next_state = (player, crate, dial, has_key)
    solved = command == "use key" and can_use_key(level, next_state)
    return next_state, pushes, wear, solved


def add_cost(left: Cost, right: Cost) -> Cost:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def solve(level: Dict[str, object]) -> List[str]:
    start = initial_state(level)
    zero: Cost = (0, 0, 0)
    inf: Cost = (10**18, 10**18, 10**18)
    dist: Dict[Node, Cost] = {start: zero}
    edges: Dict[Node, List[Tuple[str, Node, Cost]]] = {}
    reverse_edges: Dict[Node, List[Tuple[Node, Cost]]] = {}
    counter = 0
    queue: List[Tuple[Cost, int, Node]] = [(zero, counter, start)]
    solved_cost: Optional[Cost] = None

    while queue:
        cost, _, state = heapq.heappop(queue)
        if dist.get(state) != cost:
            continue
        if state == SOLVED:
            solved_cost = cost
            break

        outgoing: List[Tuple[str, Node, Cost]] = []
        for command in COMMANDS:
            result = apply_command(level, state, command)  # type: ignore[arg-type]
            if result is None:
                continue
            next_state, push_inc, wear_inc, solved = result
            edge_cost: Cost = (1, push_inc, wear_inc)
            state_key: Node = SOLVED if solved else next_state
            outgoing.append((command, state_key, edge_cost))
            reverse_edges.setdefault(state_key, []).append((state, edge_cost))
            next_cost = add_cost(cost, edge_cost)
            if next_cost < dist.get(state_key, inf):
                dist[state_key] = next_cost
                counter += 1
                heapq.heappush(queue, (next_cost, counter, state_key))
        edges[state] = outgoing

    if solved_cost is None:
        raise RuntimeError("No solution found.")

    remaining: Dict[Node, Cost] = {SOLVED: zero}
    counter = 0
    queue = [(zero, counter, SOLVED)]
    while queue:
        cost, _, state = heapq.heappop(queue)
        if remaining.get(state) != cost:
            continue
        for prev, edge_cost in reverse_edges.get(state, []):
            next_cost = add_cost(edge_cost, cost)
            if next_cost < remaining.get(prev, inf):
                remaining[prev] = next_cost
                counter += 1
                heapq.heappush(queue, (next_cost, counter, prev))

    commands: List[str] = []
    state: Node = start
    spent = zero
    while state != SOLVED:
        chosen = None
        for command, next_state, edge_cost in edges.get(state, []):
            tail_cost = remaining.get(next_state)
            if tail_cost is None:
                continue
            if add_cost(add_cost(spent, edge_cost), tail_cost) == solved_cost:
                chosen = (command, next_state, edge_cost)
                break
        if chosen is None:
            raise RuntimeError("Failed to reconstruct an optimal solution.")
        command, state, edge_cost = chosen
        commands.append(command)
        spent = add_cost(spent, edge_cost)

    return commands


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) != 3:
        raise SystemExit("Usage: python3 /app/solve.py <level.json> <output.json>")

    level = load_level(args[1])
    commands = solve(level)
    with open(args[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
