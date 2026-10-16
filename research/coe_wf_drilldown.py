"""Drill-down on the walk-forward admitted rows: independent-episode counts, quota family by horizon/side/category/year, rarity gradient inside families."""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
import runpy, io, contextlib
with contextlib.redirect_stdout(io.StringIO()): ns=runpy.run_path(os.path.join(ROOT,'research','coe_cpe_walkforward.py'))
S,pooled_base=ns['S'],ns['pooled_base']
def summ(g):
    b,n=pooled_base(g); h=g.hits.sum(); return pd.Series(dict(cond_years=len(g),entries=int(n),cpe=h/n,base=b/n,lift=(h/n)/(b/n) if b>0 else np.nan))
print('QUOTA family by horizon and side'); print(S[S.fam=='quota'].groupby(['tf','side']).apply(summ).round(3).to_string())
print('\nQUOTA family by category and q'); print(S[S.fam=='quota'].groupby(['cat','q']).apply(summ).round(3).to_string())
print('\nQUOTA family by year'); print(S[S.fam=='quota'].groupby('year').apply(summ).round(2).to_string())
print('\nFAIR / SPREAD / BIDS by horizon'); print(S[S.fam.isin(['fair','spread','bids'])].groupby(['fam','tf']).apply(summ).round(3).to_string())
# distinct test months scored per family (a rough count of independent evidence: distinct (year, month) cells hit by any admitted row)
print('\nDistinct (cat, year, month) cells scored, by family, and the distinct years behind them:')
for fam,g in S.groupby('fam'):
    cells=set(); yrs=set()
    for r in g.itertuples():
        for m in r.mo_te: cells.add((r.cat,r.year,m)); yrs.add(r.year)
    print(f'  {fam:9s} cells {len(cells):4d}  years {len(yrs):2d}')
print('\nRarity gradient inside the supply families (q = 20% vs 10%):'); print(S[S.fam.isin(['quota','fair','spread'])].groupby(['fam','q']).apply(summ).round(3).to_string())
