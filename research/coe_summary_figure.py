"""Summary figure and base rates for the COE walk-forward."""
import os, sys, warnings, io, contextlib, runpy
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
with contextlib.redirect_stdout(io.StringIO()): ns=runpy.run_path(os.path.join(ROOT,'research','coe_cpe_walkforward.py'))
Q=ns['Q']; S=ns['S']; pooled_base=ns['pooled_base']
fig,ax=plt.subplots(1,3,figsize=(16,4.8))
for cat,col in (('A','tab:blue'),('B','tab:red')): ax[0].plot(Q[cat].index,Q[cat]['premium']/1000,color=col,label=f'Category {cat}')
ax[0].set_ylabel('premium (S$ thousand), monthly mean'); ax[0].legend(); ax[0].set_title('COE premium since 2002',fontsize=9)
def lift(g):
    b,n=pooled_base(g); h=g.hits.sum(); return (h/n)/(b/n) if b>0 else np.nan, int(n)
fam=[]; 
for f,g in S.groupby('fam'): l,n=lift(g); fam.append((f,l,n))
fam=sorted(fam,key=lambda x:-x[1]); ax[1].bar([f for f,_,_ in fam],[l for _,l,_ in fam],color=['tab:green' if l>=1.4 else 'lightgray' for _,l,_ in fam]); ax[1].axhline(1,color='k',lw=.6); ax[1].axhline(1.5,color='gray',ls=':')
for i,(f,l,n) in enumerate(fam): ax[1].text(i,l+0.03,f'{n}',ha='center',fontsize=7)
ax[1].set_ylabel('walk-forward lift over base (2010-2026)'); ax[1].set_title('Which predictors worked out of sample (labels: entries scored)',fontsize=9); ax[1].tick_params(axis='x',labelsize=8)
g=S[(S.fam=='quota')&(S.side=='low')]; rows=[]
for tf,gg in g.groupby('tf'): l,n=lift(gg); b,_=pooled_base(gg); rows.append((tf,gg.hits.sum()/n,b/n,n))
x=np.arange(len(rows)); ax[2].bar(x-0.18,[r[1] for r in rows],0.36,color='tab:green',label='after a quota cut'); ax[2].bar(x+0.18,[r[2] for r in rows],0.36,color='lightgray',label='base rate'); ax[2].set_xticks(x); ax[2].set_xticklabels([f'{r[0]} month(s) ahead\n({r[3]} entries)' for r in rows],fontsize=8); ax[2].set_ylabel('probability premium is in its top 20% of moves'); ax[2].legend(fontsize=8); ax[2].set_title('Quota cuts and the premium: the effect builds over six months',fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(ROOT,'research','coe_walkforward_figure.png'),dpi=140)
# base rates for the dashboard: forward change in the monthly premium
for cat in ['A','B']:
    lp=np.log(Q[cat]['premium'].dropna())
    for nm,mask in (('all months 2002-2026',lp.index>=lp.index[0]),('last 10 years',lp.index>=pd.Timestamp('2016-10-01'))):
        out=[]
        for h in (1,3,6):
            ch=(lp.shift(-h)-lp)[mask].dropna(); out.append(f'{h}m: lower {np.mean(ch<0):.2f}, down>5% {np.mean(ch<-0.05):.2f}, up>5% {np.mean(ch>0.05):.2f}, median {np.median(ch)*100:+.1f}%')
        print(f'Category {cat}, {nm}:',' | '.join(out))
