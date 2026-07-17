#!/usr/bin/env python3
import json
import sys


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
DIRS = ("N", "E", "S", "W")
DIR_INDEX = {name: index for index, name in enumerate(DIRS)}


def parse_level(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def simulate(level, ice_cells, target_dial_index, state, command):
    length = level["length"]
    conveyor = level["conveyor"]
    plate = level["plate"]
    key_position = level["key_position"]
    goal = level["goal"]

    player, crate, dial, has_key = state
    route_open = crate == plate
    used_key = False
    push_delta = 0
    wear_delta = 0

    def can_enter(position):
        if position < 0 or position >= length:
            return False
        if position == crate:
            return False
        if position == key_position and not route_open:
            return False
        return True

    if command == "move east":
        destination = player + 1
        if not can_enter(destination):
            return None
        player = destination
    elif command == "move west":
        destination = player - 1
        if not can_enter(destination):
            return None
        player = destination
    elif command == "turn clockwise":
        dial = (dial + 1) % 4
    elif command == "turn counterclockwise":
        dial = (dial - 1) % 4
    elif command == "push east":
        destination = crate + 1
        if player + 1 != crate or destination >= length:
            return None
        crate = destination
        push_delta = 1
    elif command == "take key":
        if player != key_position or has_key:
            return None
        has_key = True
    elif command == "use key":
        if player != goal or not has_key or crate != plate or dial != target_dial_index:
            return None
        used_key = True
    elif command == "wait":
        pass
    else:
        raise ValueError(f"unknown command: {command}")

    while crate in ice_cells:
        destination = crate + 1
        if destination >= length or destination == player:
            break
        crate = destination
        wear_delta += 1

    if conveyor is not None and crate == conveyor and dial in (DIR_INDEX["E"], DIR_INDEX["W"]):
        step = 1 if dial == DIR_INDEX["E"] else -1
        destination = crate + step
        if 0 <= destination < length and destination != player:
            crate = destination

    solved = (
        used_key
        and player == goal
        and has_key
        and crate == plate
        and dial == target_dial_index
    )
    return (player, crate, dial, has_key), push_delta, wear_delta, solved


def reconstruct(parents, goal_parent, goal_command):
    commands = [goal_command]
    state = goal_parent
    while True:
        previous = parents[state]
        if previous is None:
            break
        state, command_index = previous
        commands.append(COMMANDS[command_index])
    commands.reverse()
    return commands


def solve(level):
    start = level["start"]
    start_state = (
        start["player"],
        start["crate"],
        DIR_INDEX[start["dial"]],
        bool(start["key"]),
    )
    target_dial_index = DIR_INDEX[level["target_dial"]]
    ice_cells = frozenset(level["ice"])

    visited_depth = {start_state: 0}
    parents = {start_state: None}
    costs = {start_state: (0, 0)}
    frontier = [start_state]
    depth = 0

    while frontier:
        next_candidates = {}
        best_goal = None

        for parent_rank, state in enumerate(frontier):
            base_pushes, base_wear = costs[state]
            for command in COMMANDS:
                result = simulate(level, ice_cells, target_dial_index, state, command)
                if result is None:
                    continue

                next_state, push_delta, wear_delta, solved = result
                total_pushes = base_pushes + push_delta
                total_wear = base_wear + wear_delta
                command_index = COMMAND_INDEX[command]
                lex_key = (parent_rank, command_index)

                if solved:
                    goal_key = (total_pushes, total_wear, lex_key)
                    if best_goal is None or goal_key < best_goal[0]:
                        best_goal = (goal_key, state, command)

                if next_state in visited_depth:
                    continue

                existing = next_candidates.get(next_state)
                candidate_key = (total_pushes, total_wear, lex_key)
                if existing is None or candidate_key < existing[0]:
                    next_candidates[next_state] = (
                        candidate_key,
                        state,
                        command_index,
                    )

        if best_goal is not None:
            return reconstruct(parents, best_goal[1], best_goal[2])

        if not next_candidates:
            break

        ordered = sorted(
            next_candidates.items(),
            key=lambda item: item[1][0][2],
        )
        frontier = []
        depth += 1
        for next_state, (candidate_key, parent_state, command_index) in ordered:
            visited_depth[next_state] = depth
            parents[next_state] = (parent_state, command_index)
            costs[next_state] = candidate_key[:2]
            frontier.append(next_state)

    raise RuntimeError("level is unsolvable")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 solve.py <level.json> <output.json>")

    level = parse_level(argv[1])
    commands = solve(level)
    with open(argv[2], "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv)
