#!/usr/bin/env python3
import json
import sys
import heapq
import itertools
from collections import deque


COMMANDS = (
    "move east",
    "move west",
    "push east",
    "take key",
    "turn clockwise",
    "turn counterclockwise",
    "use key",
    "wait",
)

DIALS = ("N", "E", "S", "W")
DIAL_INDEX = {dial: index for index, dial in enumerate(DIALS)}
GOAL = ("__GOAL__",)


def add_cost(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def in_bounds(length, position):
    return 0 <= position < length


def parse_level(path):
    with open(path, "r", encoding="utf-8") as handle:
        level = json.load(handle)
    start = level["start"]
    return {
        "length": level["length"],
        "conveyor": level["conveyor"],
        "ice": frozenset(level["ice"]),
        "plate": level["plate"],
        "key_position": level["key_position"],
        "goal": level["goal"],
        "target_dial": DIAL_INDEX[level["target_dial"]],
        "start_state": (
            start["player"],
            start["crate"],
            DIAL_INDEX[start["dial"]],
            bool(start["key"]),
        ),
    }


def route_open(level, crate_pos):
    return crate_pos == level["plate"]


def apply_post_phases(level, player, crate, dial, has_key):
    wear = 0

    while crate in level["ice"]:
        next_crate = crate + 1
        if not in_bounds(level["length"], next_crate) or next_crate == player:
            break
        crate = next_crate
        wear += 1

    conveyor = level["conveyor"]
    if conveyor is not None and crate == conveyor and dial in (1, 3):
        delta = 1 if dial == 1 else -1
        next_crate = crate + delta
        if in_bounds(level["length"], next_crate) and next_crate != player:
            crate = next_crate

    return (player, crate, dial, has_key), wear


def transition(level, state, command):
    player, crate, dial, has_key = state

    if command == "move east":
        dest = player + 1
        if (
            not in_bounds(level["length"], dest)
            or dest == crate
            or (dest == level["key_position"] and not route_open(level, crate))
        ):
            return None
        player = dest
    elif command == "move west":
        dest = player - 1
        if (
            not in_bounds(level["length"], dest)
            or dest == crate
            or (dest == level["key_position"] and not route_open(level, crate))
        ):
            return None
        player = dest
    elif command == "push east":
        if player != crate - 1:
            return None
        next_crate = crate + 1
        if not in_bounds(level["length"], next_crate):
            return None
        crate = next_crate
    elif command == "take key":
        if player != level["key_position"] or has_key:
            return None
        has_key = True
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "use key":
        # The public conveyor example requires plate satisfaction to be checked
        # after post-phases rather than as a precondition for issuing the command.
        if player != level["goal"] or not has_key or dial != level["target_dial"]:
            return None
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    next_state, wear = apply_post_phases(level, player, crate, dial, has_key)
    next_player, next_crate, next_dial, next_has_key = next_state
    solved = (
        command == "use key"
        and next_player == level["goal"]
        and next_has_key
        and next_crate == level["plate"]
        and next_dial == level["target_dial"]
    )
    push_cost = 1 if command == "push east" else 0
    return next_state, solved, (1, push_cost, wear)


def build_graph(level):
    start = level["start_state"]
    queue = deque([start])
    seen = {start}
    graph = {}
    reverse = {GOAL: []}

    while queue:
        state = queue.popleft()
        edges = {}
        for command in COMMANDS:
            result = transition(level, state, command)
            if result is None:
                continue
            next_state, solved, cost = result
            target = GOAL if solved else next_state
            edges[command] = (target, cost)
            reverse.setdefault(target, []).append((state, cost))
            if not solved:
                reverse.setdefault(next_state, [])
                if next_state not in seen:
                    seen.add(next_state)
                    queue.append(next_state)
        graph[state] = edges

    return graph, reverse


def shortest_to_goal(graph, reverse):
    dist = {GOAL: (0, 0, 0)}
    counter = itertools.count()
    heap = [((0, 0, 0), next(counter), GOAL)]

    while heap:
        cost, _, node = heapq.heappop(heap)
        if dist.get(node) != cost:
            continue
        for prev, edge_cost in reverse.get(node, ()):
            new_cost = add_cost(edge_cost, cost)
            if new_cost < dist.get(prev, (sys.maxsize, sys.maxsize, sys.maxsize)):
                dist[prev] = new_cost
                heapq.heappush(heap, (new_cost, next(counter), prev))

    return dist


def reconstruct(level, graph, dist):
    state = level["start_state"]
    if state not in dist:
        raise RuntimeError("level is unsolvable")

    commands = []
    while True:
        current_cost = dist[state]
        for command in COMMANDS:
            edge = graph[state].get(command)
            if edge is None:
                continue
            target, edge_cost = edge
            target_cost = dist.get(target)
            if target_cost is None:
                continue
            if add_cost(edge_cost, target_cost) == current_cost:
                commands.append(command)
                if target == GOAL:
                    return commands
                state = target
                break
        else:
            raise RuntimeError("failed to reconstruct canonical solution")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level = parse_level(argv[1])
    graph, reverse = build_graph(level)
    dist = shortest_to_goal(graph, reverse)
    commands = reconstruct(level, graph, dist)

    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
