"""Drill-down on the property walk-forward: the momentum family by horizon, side, target, window and year; episodes of independent evidence."""
import os, sys, warnings, io, contextlib, runpy
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
with contextlib.redirect_stdout(io.StringIO()): ns=runpy.run_path(os.path.join(ROOT,'research','property_cpe_walkforward.py'))
S,pooled_base=ns['S_'],ns['pooled_base']
M=S[S.fam=='momentum']
def summ(g):
    b,n=pooled_base(g); h=g.hits.sum(); return pd.Series(dict(cond_years=len(g),entries=int(n),cpe=h/n,base=b/n,lift=(h/n)/(b/n) if b>0 else np.nan))
pd.set_option('display.width',200)
print('MOMENTUM by horizon and side'); print(M.groupby(['tf','side']).apply(summ).round(3).to_string())
print('\nMOMENTUM by target'); print(M.groupby('tgt').apply(summ).round(3).to_string())
print('\nMOMENTUM by tau_p'); print(M.groupby('tp').apply(summ).round(3).to_string())
print('\nMOMENTUM by q'); print(M.groupby('q').apply(summ).round(3).to_string())
print('\nMOMENTUM by test year (lift)'); y=M.groupby('year').apply(summ); print(y[['entries','cpe','base','lift']].round(2).T.to_string())
cells=set()
for r in M.itertuples():
    for qv in r.qt_te: cells.add((r.tgt,r.year,qv))
print('\ndistinct (target, year, quarter) cells scored by momentum rows:',len(cells),'| years:',M.year.nunique())
