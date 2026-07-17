import json,sys
from collections import deque

CMDS=sorted(['move east','move west','push east','turn clockwise','turn counterclockwise','take key','use key','wait'])
def solve(level):
 n=level['length']; st=level['start']; start=(st['player'],st['crate'],{'N':0,'E':1,'S':2,'W':3}[st['dial']],bool(st['key']),0,0)
 def step(s,c):
  p,cr,d,key,push,wear=s
  if c=='move east':
   if p+1>=n or p+1==cr:return None
   p+=1
  elif c=='move west':
   if p==0 or p-1==cr:return None
   p-=1
  elif c=='push east':
   if p!=cr-1 or cr+1>=n:return None
   cr+=1;push+=1
   while cr in level['ice'] and cr+1<n:cr+=1;wear+=1
  elif c=='turn clockwise':d=(d+1)%4
  elif c=='turn counterclockwise':d=(d-1)%4
  elif c=='take key':
   if p!=level['key_position'] or key:return None
   key=True
  elif c=='use key':
   if key and p==level['goal'] and cr==level['plate'] and d==1:return ('GOAL',)
   return None
  elif c!='wait':return None
  if cr==level.get('conveyor') and d==1 and cr+1<n and cr+1!=p:cr+=1
  return (p,cr,d,key,push,wear)
 q=deque([(start,[])]); seen={start}
 while q:
  s,path=q.popleft()
  for c in CMDS:
   t=step(s,c)
   if t==('GOAL',):return path+[c]
   if t is not None and t not in seen:
    seen.add(t);q.append((t,path+[c]))
 raise RuntimeError('unsolved level')
level=json.load(open(sys.argv[1])); json.dump({'commands':solve(level)},open(sys.argv[2],'w'),separators=(',',':'))
