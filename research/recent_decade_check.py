"""Do the supported families still beat the base rate in the latest decade of test years (2017 onward)? Property and COE."""
import os, sys, warnings, io, contextlib, runpy
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
def run(path):
    with contextlib.redirect_stdout(io.StringIO()): return runpy.run_path(os.path.join(ROOT,'research',path))
for name,path,skey,fkey in (('PROPERTY','property_cpe_walkforward.py','S_','fam'),('COE','coe_cpe_walkforward.py','S','fam')):
    ns=run(path); S=ns[skey]; pb=ns['pooled_base']
    def lift(g):
        if len(g)==0: return (np.nan,0)
        b,n=pb(g); h=g.hits.sum(); return ((h/n)/(b/n) if b>0 else np.nan, int(n))
    print(f'\n{name}: pooled lift by family, all test years vs 2017 onward vs 2007-2016 (entries in brackets)')
    for fam,g in S.groupby(fkey):
        a=lift(g); r=lift(g[g.year>=2017]); e=lift(g[g.year<=2016]); print(f'  {fam:12s} all {a[0]:5.2f} ({a[1]:4d}) | 2017+ {r[0]:5.2f} ({r[1]:4d}) | up to 2016 {e[0]:5.2f} ({e[1]:4d})')
    a=lift(S); r=lift(S[S.year>=2017]); print(f'  {"ALL":12s} all {a[0]:5.2f} ({a[1]:4d}) | 2017+ {r[0]:5.2f} ({r[1]:4d})')
    if name=='COE':
        q=S[(S.fam=="quota")&(S.side=="low")]
        for tf,g in q.groupby('tf'):
            a=lift(g); r=lift(g[g.year>=2017]); print(f'   quota cut, tf={tf}: all {a[0]:.2f} ({a[1]}) | 2017+ {r[0]:.2f} ({r[1]})')
