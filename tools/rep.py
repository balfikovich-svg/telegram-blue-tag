#!/usr/bin/env python3
# usage: rep.py FILE <<< "OLD\n===\nNEW\n%%%\nOLD2\n===\nNEW2"
import sys
p=sys.argv[1]; s=open(p).read()
for blk in sys.stdin.read().split('\n%%%\n'):
    old,new=blk.split('\n===\n')
    new=new.rstrip('\n') if not old.endswith('\n') else new
    c=s.count(old)
    if c!=1: sys.exit(f'{p}: {c} matches for:\n{old[:200]}')
    s=s.replace(old,new)
open(p,'w').write(s); print('ok',p)
