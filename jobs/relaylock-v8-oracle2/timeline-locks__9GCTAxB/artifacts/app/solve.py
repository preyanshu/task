import heapq,json,sys

CMDS=sorted(['move east','move west','push east','take key','turn clockwise','turn counterclockwise','use key','wait'])

def solve(level):
 n=level['length']; st=level['start']
 start=(st['player'],st['crate'],{'N':0,'E':1,'S':2,'W':3}[st['dial']],bool(st['key']))

 def can_enter(pos,cr,key):
  if pos<0 or pos>=n or pos==cr:return False
  if pos==level['key_position'] and (not key) and cr!=level['plate']:return False
  return True

 pq=[((0,0,0,()),start)]
 best={start:(0,0,0,())}
 while pq:
  cost,state=heapq.heappop(pq)
  if best.get(state)!=cost:continue
  p,cr,d,key=state
  for c in CMDS:
   np,nc,nd,nkey=p,cr,d,key
   add_push=add_wear=0
   if c=='move east':
    if not can_enter(np+1,nc,nkey):continue
    np+=1
   elif c=='move west':
    if not can_enter(np-1,nc,nkey):continue
    np-=1
   elif c=='push east':
    if np!=nc-1 or nc+1>=n:continue
    nc+=1; add_push=1
    while nc in level['ice'] and nc+1<n and nc+1!=np:
     nc+=1; add_wear+=1
   elif c=='turn clockwise': nd=(nd+1)%4
   elif c=='turn counterclockwise': nd=(nd-1)%4
   elif c=='take key':
    if np!=level['key_position'] or nkey:continue
    nkey=True
   elif c=='use key':
    if nkey and np==level['goal'] and nc==level['plate'] and nd==1:
     return list(cost[3]+(c,))
    continue
   elif c!='wait':
    continue
   if nc==level.get('conveyor'):
    delta=1 if nd==1 else -1 if nd==3 else 0
    nxt=nc+delta
    if delta and 0<=nxt<n and nxt!=np:nc=nxt
   new_cost=(cost[0]+1,cost[1]+add_push,cost[2]+add_wear,cost[3]+(c,))
   new_state=(np,nc,nd,nkey)
   if new_cost<best.get(new_state,(10**9,10**9,10**9,('~',))):
    best[new_state]=new_cost
    heapq.heappush(pq,(new_cost,new_state))
 raise RuntimeError('unsolved level')

level=json.load(open(sys.argv[1])); json.dump({'commands':solve(level)},open(sys.argv[2],'w'),separators=(',',':'))
