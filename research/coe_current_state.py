"""Where each registered predictor stands in September 2026 (latest month), with its percentile against all earlier months, and whether it is in a tail that the walk-forward admitted."""
import os, sys, warnings, io, contextlib, runpy
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
with contextlib.redirect_stdout(io.StringIO()): ns=runpy.run_path(os.path.join(ROOT,'research','coe_cpe_walkforward.py'))
build_X,fair_resid,Q=ns['build_X'],ns['fair_resid'],ns['Q']
last=Q['A'].index[-1]; print('latest month in the panel:',last.date())
for cat in ['A','B']:
    lp,lq,X,SIGN=build_X(cat); X[('fair',0)]=fair_resid(lp,lq,last.year+1)
    print(f'\nCategory {cat}: premium {Q[cat]["premium"].iloc[-1]:,.0f} (prevailing {Q[cat]["pqp"].iloc[-1]:,.0f}); 12-month high {Q[cat]["premium"].iloc[-12:].max():,.0f}, low {Q[cat]["premium"].iloc[-12:].min():,.0f}; all-time high {Q[cat]["premium"].max():,.0f}')
    for (fam,tp),xs in sorted(X.items(),key=lambda kv:(kv[0][0],kv[0][1])):
        if fam in ('rates','dereg','momentum'): continue
        v=xs.iloc[-1]; hist=xs.iloc[:-1].dropna(); pct=(hist<v).mean()*100 if pd.notna(v) else np.nan
        implied=('premium LOWER' if (SIGN[fam]>0)==(pct<50) else 'premium HIGHER') if pd.notna(pct) else ''
        flag='  <-- in a 20% tail' if pd.notna(pct) and (pct<=20 or pct>=80) else ''
        print(f'  {fam:7s} tau_p={tp:2d}  value {v:8.3f}  percentile {pct:5.0f}{flag}')
