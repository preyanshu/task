import heapq
import json, subprocess, tempfile
from pathlib import Path
import pytest

ROOT=Path('/app'); LEVELS=json.loads((Path('/tests')/'hidden_cases.json').read_text())['levels']
CMDS=sorted(['move east','move west','push east','take key','turn clockwise','turn counterclockwise','use key','wait'])

def run_solver(level):
    with tempfile.TemporaryDirectory() as d:
        inp=Path(d)/'level.json'; out=Path(d)/'out.json'; inp.write_text(json.dumps(level))
        p=subprocess.run(['python3','/app/solve.py',str(inp),str(out)],capture_output=True,text=True,timeout=10)
        assert p.returncode==0,p.stderr
        data=json.loads(out.read_text()); assert type(data) is dict and set(data)=={'commands'}
        return data['commands']

def can_enter_key(level, crate):
    return crate == level['plate']

def replay(level,commands):
    n=level['length']; s=dict(level['start']); dial={'N':0,'E':1,'S':2,'W':3}[s['dial']]; target={'N':0,'E':1,'S':2,'W':3}[level['target_dial']]; crate=s['crate']; player=s['player']; key=s['key']; wear=pushes=0

    def can_player_enter(pos, crate_pos):
        if pos < 0 or pos >= n or pos == crate_pos:
            return False
        if pos == level['key_position'] and not can_enter_key(level, crate_pos):
            return False
        return True

    for i,c in enumerate(commands,1):
        if c=='turn clockwise': dial=(dial+1)%4
        elif c=='turn counterclockwise': dial=(dial-1)%4
        elif c=='move east':
            if not can_player_enter(player+1, crate): raise AssertionError(f'illegal {i}')
            player+=1
        elif c=='move west':
            if not can_player_enter(player-1, crate): raise AssertionError(f'illegal {i}')
            player-=1
        elif c=='push east':
            if player!=crate-1 or crate+1>=n: raise AssertionError(f'illegal {i}')
            crate+=1; pushes+=1
            while crate in level['ice'] and crate+1<n and crate+1!=player:
                crate+=1
                wear+=1
        elif c=='take key':
            if player!=level['key_position'] or key: raise AssertionError(f'illegal {i}')
            key=True
        elif c=='use key':
            if not(key and player==level['goal'] and crate==level['plate'] and dial==target): raise AssertionError(f'illegal {i}')
        elif c!='wait': raise AssertionError(f'unknown {i}')
        while crate in level['ice'] and crate+1<n and crate+1!=player:
            crate+=1
            wear+=1
        if crate==level.get('conveyor'):
            delta = 1 if dial==1 else -1 if dial==3 else 0
            nxt = crate + delta
            if delta and 0 <= nxt < n and nxt != player:
                crate = nxt
        if c=='use key' and key and player==level['goal'] and crate==level['plate'] and dial==target:
            return (True,pushes,wear)
    return (False,pushes,wear)

def canonical(level):
    n=level['length']; s=level['start']; target={'N':0,'E':1,'S':2,'W':3}[level['target_dial']]
    start=(s['player'], s['crate'], {'N':0,'E':1,'S':2,'W':3}[s['dial']], bool(s['key']))
    pq=[((0,0,0,()), start)]
    best={start:(0,0,0,())}

    def can_player_enter(pos, crate_pos):
        if pos < 0 or pos >= n or pos == crate_pos:
            return False
        if pos == level['key_position'] and crate_pos != level['plate']:
            return False
        return True

    while pq:
        cost, state = heapq.heappop(pq)
        if best.get(state) != cost:
            continue
        player, crate, dial, key = state
        for cmd in CMDS:
            p, cr, d, has_key = player, crate, dial, key
            add_push = add_wear = 0
            if cmd == 'move east':
                if not can_player_enter(p+1, cr):
                    continue
                p += 1
            elif cmd == 'move west':
                if not can_player_enter(p-1, cr):
                    continue
                p -= 1
            elif cmd == 'push east':
                if p != cr-1 or cr+1 >= n:
                    continue
                cr += 1
                add_push = 1
                while cr in level['ice'] and cr+1 < n and cr+1 != p:
                    cr += 1
                    add_wear += 1
            elif cmd == 'turn clockwise':
                d = (d+1) % 4
            elif cmd == 'turn counterclockwise':
                d = (d-1) % 4
            elif cmd == 'take key':
                if has_key or p != level['key_position']:
                    continue
                has_key = True
            elif cmd == 'use key':
                if not (has_key and p == level['goal'] and cr == level['plate'] and d == target):
                    continue
            elif cmd != 'wait':
                continue

            while cr in level['ice'] and cr+1 < n and cr+1 != p:
                cr += 1
                add_wear += 1

            if cr == level.get('conveyor'):
                delta = 1 if d==1 else -1 if d==3 else 0
                nxt = cr + delta
                if delta and 0 <= nxt < n and nxt != p:
                    cr = nxt

            if cmd == 'use key' and has_key and p == level['goal'] and cr == level['plate'] and d == target:
                return list(cost[3] + (cmd,))

            new_cost=(cost[0]+1, cost[1]+add_push, cost[2]+add_wear, cost[3]+(cmd,))
            new_state=(p,cr,d,has_key)
            if new_cost < best.get(new_state, (10**9,10**9,10**9,('~',))):
                best[new_state]=new_cost
                heapq.heappush(pq,(new_cost,new_state))
    raise AssertionError(level['id'])

def test_all_hidden_levels_solve_and_are_canonical():
    for level in LEVELS:
        commands=run_solver(level)
        result=replay(level,commands)
        assert result[0],level['id']
        assert commands == canonical(level), level['id']

def test_pre_key_dial_is_part_of_state():
    level=LEVELS[0]
    wrong=['take key','turn counterclockwise','use key']
    with pytest.raises(AssertionError):
        replay(level,wrong)
