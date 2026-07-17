#!/usr/bin/env python3
import json
import sys
from collections import defaultdict, deque
from heapq import heappop, heappush


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

DIALS = ["N", "E", "S", "W"]
DIAL_INDEX = {dial: idx for idx, dial in enumerate(DIALS)}
SOLVED = "__SOLVED__"


def add_cost(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


class Solver:
    def __init__(self, level):
        self.length = level["length"]
        start = level["start"]
        self.start = (
            start["player"],
            start["crate"],
            DIAL_INDEX[start["dial"]],
            bool(start["key"]),
        )
        self.conveyor = level["conveyor"]
        self.ice = frozenset(level["ice"])
        self.plate = level["plate"]
        self.key_position = level["key_position"]
        self.goal = level["goal"]
        self.target_dial = DIAL_INDEX[level["target_dial"]]

    def route_open(self, crate):
        return crate == self.plate

    def in_bounds(self, pos):
        return 0 <= pos < self.length

    def apply_phases(self, player, crate, dial, has_key):
        wear = 0

        # The level schema carries no latent slide-direction state, so the slide
        # phase is modeled as repeated eastward motion while the crate remains on ice.
        while crate in self.ice:
            next_crate = crate + 1
            if not self.in_bounds(next_crate) or next_crate == player:
                return None
            crate = next_crate
            if crate in self.ice:
                wear += 1

        if self.conveyor is not None and crate == self.conveyor and dial in (
            DIAL_INDEX["E"],
            DIAL_INDEX["W"],
        ):
            delta = 1 if dial == DIAL_INDEX["E"] else -1
            dest = crate + delta
            if self.in_bounds(dest) and dest != player:
                crate = dest

        return (player, crate, dial, has_key), wear

    def step(self, state, command):
        player, crate, dial, has_key = state
        route_open = self.route_open(crate)

        if command == "move east":
            new_player = player + 1
            if (
                not self.in_bounds(new_player)
                or new_player == crate
                or (new_player == self.key_position and not route_open)
            ):
                return None
            primary = (new_player, crate, dial, has_key)
        elif command == "move west":
            new_player = player - 1
            if (
                not self.in_bounds(new_player)
                or new_player == crate
                or (new_player == self.key_position and not route_open)
            ):
                return None
            primary = (new_player, crate, dial, has_key)
        elif command == "turn clockwise":
            primary = (player, crate, (dial + 1) % 4, has_key)
        elif command == "turn counterclockwise":
            primary = (player, crate, (dial - 1) % 4, has_key)
        elif command == "push east":
            if player + 1 != crate:
                return None
            new_crate = crate + 1
            if not self.in_bounds(new_crate):
                return None
            primary = (player, new_crate, dial, has_key)
        elif command == "take key":
            if has_key or player != self.key_position:
                return None
            primary = (player, crate, dial, True)
        elif command == "use key":
            if (
                player == self.goal
                and has_key
                and crate == self.plate
                and dial == self.target_dial
            ):
                return SOLVED, (1, 0, 0)
            return None
        elif command == "wait":
            primary = (player, crate, dial, has_key)
        else:
            raise ValueError(f"unknown command: {command}")

        phased = self.apply_phases(*primary)
        if phased is None:
            return None
        next_state, wear = phased
        push_cost = 1 if command == "push east" else 0
        return next_state, (1, push_cost, wear)

    def build_graph(self):
        graph = {}
        reverse = defaultdict(list)
        seen = {self.start}
        queue = deque([self.start])

        while queue:
            state = queue.popleft()
            edges = []
            for command in COMMANDS:
                result = self.step(state, command)
                if result is None:
                    continue
                succ, cost = result
                edges.append((command, succ, cost))
                reverse[succ].append((state, cost))
                if succ != SOLVED and succ not in seen:
                    seen.add(succ)
                    queue.append(succ)
            graph[state] = edges

        graph[SOLVED] = []
        return graph, reverse

    def shortest_to_goal(self, reverse):
        distances = {SOLVED: (0, 0, 0)}
        heap = [(0, 0, 0, 0, SOLVED)]
        counter = 1

        while heap:
            steps, pushes, wear, _, node = heappop(heap)
            dist = (steps, pushes, wear)
            if dist != distances.get(node):
                continue
            for pred, edge_cost in reverse.get(node, []):
                cand = add_cost(edge_cost, dist)
                if pred not in distances or cand < distances[pred]:
                    distances[pred] = cand
                    heappush(heap, (cand[0], cand[1], cand[2], counter, pred))
                    counter += 1

        return distances

    def reconstruct(self, graph, distances):
        if self.start not in distances:
            raise ValueError("level is unsolved from the start state")

        commands = []
        state = self.start
        while state != SOLVED:
            best = None
            for command, succ, edge_cost in graph[state]:
                succ_dist = distances.get(succ)
                if succ_dist is None:
                    continue
                if add_cost(edge_cost, succ_dist) == distances[state]:
                    best = (command, succ)
                    break
            if best is None:
                raise RuntimeError("failed to reconstruct an optimal transcript")
            command, state = best
            commands.append(command)
        return commands

    def solve(self):
        graph, reverse = self.build_graph()
        distances = self.shortest_to_goal(reverse)
        return self.reconstruct(graph, distances)


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    input_path, output_path = argv[1], argv[2]
    with open(input_path, "r", encoding="utf-8") as fh:
        level = json.load(fh)

    commands = Solver(level).solve()

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump({"commands": commands}, fh, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
