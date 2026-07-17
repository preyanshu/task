#!/usr/bin/env python3
import json
import sys
from collections import defaultdict


COMMANDS = [
    "move east",
    "move west",
    "push east",
    "take key",
    "turn clockwise",
    "turn counterclockwise",
    "use key",
    "wait",
]

CW = {"N": "E", "E": "S", "S": "W", "W": "N"}
CCW = {value: key for key, value in CW.items()}
DIR_DELTA = {"E": 1, "W": -1}


def load_level(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_answer(path, commands):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"commands": commands}, handle, separators=(",", ":"))


def route_open(level, crate_pos):
    return crate_pos == level["plate"]


def can_enter_key(level, crate_pos):
    return route_open(level, crate_pos)


def slide_crate(level, player_pos, crate_pos, momentum):
    wear = 0
    if momentum == 0:
        return crate_pos, momentum, wear

    while crate_pos in level["ice_set"]:
        next_pos = crate_pos + momentum
        if next_pos < 0 or next_pos >= level["length"] or next_pos == player_pos:
            break
        crate_pos = next_pos
        if crate_pos in level["ice_set"]:
            wear += 1

    return crate_pos, momentum, wear


def conveyor_move(level, player_pos, crate_pos, momentum, dial):
    conveyor = level["conveyor"]
    if conveyor is None or crate_pos != conveyor or dial not in DIR_DELTA:
        return crate_pos, momentum

    delta = DIR_DELTA[dial]
    next_pos = crate_pos + delta
    if next_pos < 0 or next_pos >= level["length"] or next_pos == player_pos:
        return crate_pos, momentum

    return next_pos, delta


def apply_command(level, state, command):
    player_pos, crate_pos, dial, has_key, momentum = state
    new_player = player_pos
    new_crate = crate_pos
    new_dial = dial
    new_key = has_key
    new_momentum = momentum
    push_cost = 0

    if command == "move east":
        dest = player_pos + 1
        if dest >= level["length"] or dest == crate_pos:
            return None
        if dest == level["key_position"] and not can_enter_key(level, crate_pos):
            return None
        new_player = dest
    elif command == "move west":
        dest = player_pos - 1
        if dest < 0 or dest == crate_pos:
            return None
        if dest == level["key_position"] and not can_enter_key(level, crate_pos):
            return None
        new_player = dest
    elif command == "turn clockwise":
        new_dial = CW[dial]
    elif command == "turn counterclockwise":
        new_dial = CCW[dial]
    elif command == "push east":
        if player_pos + 1 != crate_pos:
            return None
        dest = crate_pos + 1
        if dest >= level["length"]:
            return None
        new_crate = dest
        new_momentum = 1
        push_cost = 1
    elif command == "take key":
        if has_key or player_pos != level["key_position"]:
            return None
        new_key = True
    elif command == "use key":
        if (
            player_pos != level["goal"]
            or not has_key
            or crate_pos != level["plate"]
            or dial != level["target_dial"]
        ):
            return None
        return {"solved": True, "pushes": 0, "wear": 0}
    elif command == "wait":
        pass
    else:
        raise ValueError(f"Unknown command: {command}")

    new_crate, new_momentum, wear = slide_crate(
        level, new_player, new_crate, new_momentum
    )
    new_crate, new_momentum = conveyor_move(
        level, new_player, new_crate, new_momentum, new_dial
    )

    return {
        "solved": False,
        "state": (new_player, new_crate, new_dial, new_key, new_momentum),
        "pushes": push_cost,
        "wear": wear,
    }


def solve(level):
    level = dict(level)
    level["ice_set"] = frozenset(level["ice"])
    start = level["start"]
    initial_state = (
        start["player"],
        start["crate"],
        start["dial"],
        bool(start["key"]),
        0,
    )

    command_ids = list(range(len(COMMANDS)))
    seen_depth = {initial_state: 0}
    frontier = {initial_state: (0, 0, ())}
    depth = 0

    while frontier:
        solution_labels = []
        next_frontier = {}

        for state, (pushes, wear, path) in frontier.items():
            for command_id in command_ids:
                command = COMMANDS[command_id]
                result = apply_command(level, state, command)
                if result is None:
                    continue

                next_path = path + (command_id,)
                next_pushes = pushes + result["pushes"]
                next_wear = wear + result["wear"]
                label = (next_pushes, next_wear, next_path)

                if result["solved"]:
                    solution_labels.append(label)
                    continue

                next_state = result["state"]
                prior_depth = seen_depth.get(next_state)
                if prior_depth is not None and prior_depth < depth + 1:
                    continue

                existing = next_frontier.get(next_state)
                if existing is None or label < existing:
                    next_frontier[next_state] = label

        if solution_labels:
            best = min(solution_labels)
            return [COMMANDS[idx] for idx in best[2]]

        depth += 1
        for state in next_frontier:
            seen_depth.setdefault(state, depth)
        frontier = next_frontier

    raise ValueError("No solution found")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python3 /app/solve.py <level.json> <output.json>")

    level = load_level(argv[1])
    commands = solve(level)
    dump_answer(argv[2], commands)


if __name__ == "__main__":
    main(sys.argv)
