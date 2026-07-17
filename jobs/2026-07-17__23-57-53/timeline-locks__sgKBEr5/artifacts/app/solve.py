#!/usr/bin/env python3
import heapq
import json
import sys


CMDS = sorted([
    'move east', 'move west', 'push east', 'take key',
    'turn clockwise', 'turn counterclockwise', 'use key', 'wait'
])
DIAL = {'N': 0, 'E': 1, 'S': 2, 'W': 3}


def solve(level):
    n = level['length']
    ice = set(level['ice'])
    conveyor = level.get('conveyor')
    plate = level['plate']
    key_position = level['key_position']
    goal = level['goal']
    start_raw = level['start']
    target = DIAL[level['target_dial']]
    start = (
        start_raw['player'],
        start_raw['crate'],
        DIAL[start_raw['dial']],
        bool(start_raw['key']),
    )

    def can_enter(pos, crate):
        if pos < 0 or pos >= n or pos == crate:
            return False
        if pos == key_position and crate != plate:
            return False
        return True

    def step(state, cmd):
        player, crate, dial, has_key = state
        pushes = wear = 0

        if cmd == 'move east':
            if not can_enter(player + 1, crate):
                return None
            player += 1
        elif cmd == 'move west':
            if not can_enter(player - 1, crate):
                return None
            player -= 1
        elif cmd == 'push east':
            if player != crate - 1 or crate + 1 >= n:
                return None
            crate += 1
            pushes = 1
        elif cmd == 'take key':
            if has_key or player != key_position:
                return None
            has_key = True
        elif cmd == 'turn clockwise':
            dial = (dial + 1) % 4
        elif cmd == 'turn counterclockwise':
            dial = (dial - 1) % 4
        elif cmd == 'use key':
            if not (has_key and player == goal and crate == plate and dial == target):
                return None
        elif cmd != 'wait':
            return None

        while crate in ice and crate + 1 < n and crate + 1 != player:
            crate += 1
            wear += 1

        if crate == conveyor:
            delta = 1 if dial == DIAL['E'] else -1 if dial == DIAL['W'] else 0
            nxt = crate + delta
            if delta and 0 <= nxt < n and nxt != player:
                crate = nxt

        solved = cmd == 'use key' and has_key and player == goal and crate == plate and dial == target
        return (player, crate, dial, has_key), pushes, wear, solved

    pq = [((0, 0, 0, ()), start)]
    best = {start: (0, 0, 0, ())}
    while pq:
        cost, state = heapq.heappop(pq)
        if best.get(state) != cost:
            continue
        for cmd in CMDS:
            result = step(state, cmd)
            if result is None:
                continue
            next_state, pushes, wear, solved = result
            next_cost = (cost[0] + 1, cost[1] + pushes, cost[2] + wear, cost[3] + (cmd,))
            if solved:
                return list(next_cost[3])
            if next_cost < best.get(next_state, (10**9, 10**9, 10**9, ('~',))):
                best[next_state] = next_cost
                heapq.heappush(pq, (next_cost, next_state))
    raise RuntimeError('level is unsolvable')


def main(argv):
    if len(argv) != 3:
        raise SystemExit('usage: python3 /app/solve.py <level.json> <output.json>')
    with open(argv[1], 'r', encoding='utf-8') as f:
        level = json.load(f)
    with open(argv[2], 'w', encoding='utf-8') as f:
        json.dump({'commands': solve(level)}, f, separators=(',', ':'))


if __name__ == '__main__':
    main(sys.argv)
