#!/usr/bin/env python3
import heapq
import json
import sys
from collections import defaultdict, deque


DIALS = "NESW"
DIAL_TO_INDEX = {dial: index for index, dial in enumerate(DIALS)}
GOAL_STATE = (-1, -1, -1, -1)
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


def add_cost(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


class Level:
    def __init__(self, data):
        start = data["start"]
        self.length = data["length"]
        self.start_state = (
            start["player"],
            start["crate"],
            DIAL_TO_INDEX[start["dial"]],
            1 if start["key"] else 0,
        )
        self.conveyor = data["conveyor"]
        self.ice = set(data["ice"])
        self.plate = data["plate"]
        self.key_position = data["key_position"]
        self.goal = data["goal"]
        self.target_dial = DIAL_TO_INDEX[data["target_dial"]]

    def route_open(self, crate):
        return crate == self.plate

    def in_bounds(self, pos):
        return 0 <= pos < self.length

    def simulate(self, state, command):
        player, crate, dial, has_key = state

        if command == "move east":
            target = player + 1
            if not self.in_bounds(target) or target == crate:
                return None
            if target == self.key_position and not self.route_open(crate):
                return None
            player = target
        elif command == "move west":
            target = player - 1
            if not self.in_bounds(target) or target == crate:
                return None
            if target == self.key_position and not self.route_open(crate):
                return None
            player = target
        elif command == "turn clockwise":
            dial = (dial + 1) % 4
        elif command == "turn counterclockwise":
            dial = (dial - 1) % 4
        elif command == "push east":
            target = crate + 1
            if player != crate - 1 or not self.in_bounds(target):
                return None
            crate = target
        elif command == "take key":
            if player != self.key_position:
                return None
            has_key = 1
        elif command == "use key":
            if (
                player == self.goal
                and has_key
                and crate == self.plate
                and dial == self.target_dial
            ):
                return GOAL_STATE, (1, 0, 0)
            return None
        elif command == "wait":
            pass
        else:
            raise ValueError(f"unknown command: {command}")

        wear = 0
        while crate in self.ice:
            next_crate = crate + 1
            if not self.in_bounds(next_crate):
                return None
            crate = next_crate
            wear += 1

        if self.conveyor is not None and crate == self.conveyor:
            if dial == DIAL_TO_INDEX["E"]:
                next_crate = crate + 1
                if self.in_bounds(next_crate) and next_crate != player:
                    crate = next_crate
            elif dial == DIAL_TO_INDEX["W"]:
                next_crate = crate - 1
                if self.in_bounds(next_crate) and next_crate != player:
                    crate = next_crate

        next_state = (player, crate, dial, has_key)
        push_cost = 1 if command == "push east" else 0
        return next_state, (1, push_cost, wear)


def build_graph(level):
    edges = {}
    reverse_edges = defaultdict(list)
    queue = deque([level.start_state])
    seen = {level.start_state}

    while queue:
        state = queue.popleft()
        state_edges = []
        for command in COMMANDS:
            result = level.simulate(state, command)
            if result is None:
                continue
            next_state, edge_cost = result
            state_edges.append((command, next_state, edge_cost))
            reverse_edges[next_state].append((state, edge_cost))
            if next_state != GOAL_STATE and next_state not in seen:
                seen.add(next_state)
                queue.append(next_state)
        edges[state] = state_edges

    return edges, reverse_edges


def reverse_dijkstra(reverse_edges):
    dist = {GOAL_STATE: (0, 0, 0)}
    heap = [(0, 0, 0, GOAL_STATE)]

    while heap:
        steps, pushes, wear, state = heapq.heappop(heap)
        current = (steps, pushes, wear)
        if current != dist.get(state):
            continue
        for prev_state, edge_cost in reverse_edges.get(state, []):
            candidate = add_cost(current, edge_cost)
            if candidate < dist.get(prev_state, (float("inf"),) * 3):
                dist[prev_state] = candidate
                heapq.heappush(heap, (candidate[0], candidate[1], candidate[2], prev_state))

    return dist


def reconstruct(level, edges, dist):
    if level.start_state not in dist:
        raise ValueError("level is unsolved under the published rules")

    state = level.start_state
    commands = []

    while state != GOAL_STATE:
        target_cost = dist[state]
        chosen = None
        for command, next_state, edge_cost in edges[state]:
            next_cost = dist.get(next_state)
            if next_cost is None:
                continue
            if add_cost(edge_cost, next_cost) == target_cost:
                chosen = (command, next_state)
                break
        if chosen is None:
            raise ValueError("failed to reconstruct canonical solution")
        command, state = chosen
        commands.append(command)

    return commands


def solve(level_data):
    level = Level(level_data)
    edges, reverse_edges = build_graph(level)
    dist = reverse_dijkstra(reverse_edges)
    return reconstruct(level, edges, dist)


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as f:
        level_data = json.load(f)

    commands = solve(level_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"commands": commands}, f, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
