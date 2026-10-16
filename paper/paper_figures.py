"""Figures for the paper (paper/figs/). Reads the committed data, research outputs and paper/numbers.json.  python paper/paper_figures.py"""
import json, os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import panel, property_panel as pp
OUT = os.path.join(ROOT, 'paper', 'figs'); os.makedirs(OUT, exist_ok=True); N = json.load(open(os.path.join(ROOT, 'paper', 'numbers.json')))
plt.rcParams.update({'font.family': 'serif', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .25, 'figure.dpi': 150})
A_, B_, GR, GD, RD, BL = '#1f4e79', '#b5651d', '#7a7a7a', '#2e7d32', '#b23a48', '#3b6ea8'
Q = panel.quota_panel(); F = panel.flows()
# 1. premium and quota
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
for c, col in (('A', A_), ('B', B_)): ax[0].plot(Q[c].index, Q[c]['premium'] / 1000, color=col, lw=1.3, label=f'Category {c}'); ax[1].plot(Q[c].index, Q[c]['quota'], color=col, lw=1.3)
ax[0].set_ylabel('premium, S$ thousand (monthly mean)'); ax[0].legend(frameon=False); ax[0].set_title('COE premium', fontsize=9); ax[1].set_ylabel('quota per month (two rounds)'); ax[1].set_title('COE quota', fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'fig1_coe.png'), dpi=200); plt.close()
# 2. supply echo
nr = F['newreg_A'] + F['newreg_B']; dr = F['dereg_A'] + F['dereg_B']; sch = nr.copy(); sch.index = nr.index + pd.DateOffset(months=120)
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw=dict(width_ratios=[1.6, 1]))
w = lambda s: s[(s.index >= '2002-01-01') & (s.index <= '2030-01-01')]
ax[0].plot(w(nr.rolling(6).mean()).index, w(nr.rolling(6).mean()), color=GR, lw=1, label='new registrations'); ax[0].plot(w(dr.rolling(6).mean()).index, w(dr.rolling(6).mean()), color=A_, lw=1.4, label='de-registrations'); ax[0].plot(w(sch.rolling(6).mean()).index, w(sch.rolling(6).mean()), color=GD, lw=1.4, ls='--', label='scheduled expiries (registrations ten years earlier)')
ax[0].set_ylabel('vehicles per month (6-month mean)'); ax[0].set_ylim(0, 12500); ax[0].legend(frameon=False, fontsize=7, loc='upper center'); ax[0].set_title('The ten-year echo', fontsize=9)
for c, col in (('A', A_), ('B', B_)): ks = sorted(N[f'lagcorr_{c}'], key=int); ax[1].plot([int(k) for k in ks], [N[f'lagcorr_{c}'][k] for k in ks], color=col, marker='o', ms=3, label=f'Category {c}')
ax[1].axhline(0, color='k', lw=.6); ax[1].set_xlabel('months the supply cycle leads'); ax[1].set_ylabel('correlation with detrended log premium'); ax[1].legend(frameon=False, fontsize=7); ax[1].set_title('Premium lags supply', fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'fig2_echo.png'), dpi=200); plt.close()
# 3. COE families
S = pd.DataFrame(N['coe_support']).T.drop(index=['fair'], errors='ignore'); S = S.sort_values('lift_all', ascending=False); lab = {'quota': 'quota', 'bids': 'bids / quota', 'spread': 'B/A spread', 'momentum': 'momentum', 'supplycycle': 'supply cycle', 'dereg': 'de-registrations', 'rates': 'interest rates'}
fig, ax = plt.subplots(figsize=(7.2, 3.1)); x = np.arange(len(S)); wd = .38
ax.bar(x - wd / 2, S['lift_all'].astype(float), wd, color=A_, label='all test years'); ax.bar(x + wd / 2, S['lift_2017'].astype(float).fillna(0), wd, color=B_, label='2017 onward')
for i, (a, b, na, nb) in enumerate(zip(S['lift_all'], S['lift_2017'], S['entries_all'], S['entries_2017'])): ax.text(i - wd / 2, float(a) + .04, f'{int(na)}', ha='center', fontsize=6.5); ax.text(i + wd / 2, (0 if pd.isna(b) else float(b)) + .04, f'{int(nb)}', ha='center', fontsize=6.5)
ax.axhline(1, color='k', lw=.8); ax.axhline(1.4, color=RD, lw=.8, ls=':'); ax.set_xticks(x); ax.set_xticklabels([lab.get(i, i) for i in S.index], fontsize=8); ax.set_ylabel('out-of-sample lift over base rate'); ax.legend(frameon=False); ax.set_title('COE: lift by predictor family (labels: scored entries; dotted line: support threshold)', fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'fig3_coe_families.png'), dpi=200); plt.close()
# 4. quota-cut effect
thr = pd.DataFrame(N['rob_thr']); m = thr[(thr.q == 0.2) & (thr.yq == 0.2)].sort_values('tf'); sub = pd.DataFrame(N['rob_sub'])
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0)); x = np.arange(3); wd = .38
ax[0].bar(x - wd / 2, m['cpe'], wd, color=A_, label='after a quota cut'); ax[0].bar(x + wd / 2, m['base'], wd, color=GR, label='base rate')
for i, r in enumerate(m.itertuples()): ax[0].text(i, r.cpe + .01, f'n={int(r.entries)}', ha='center', fontsize=7)
ax[0].set_xticks(x); ax[0].set_xticklabels([f'{int(t)} months' for t in m.tf]); ax[0].set_ylabel('probability of a top-20% premium rise'); ax[0].legend(frameon=False, fontsize=7); ax[0].set_title('Quota cut and the premium', fontsize=9)
per = ['2010-2016', '2017-2021', '2022-2026']; cols = [A_, BL, RD]
for j, (p_, c_) in enumerate(zip(per, cols)):
    s = sub[sub.period == p_].sort_values('tf'); ax[1].bar(x + (j - 1) * .26, s['lift'].fillna(0), .26, color=c_, label=p_)
    for i, r in enumerate(s.itertuples()): ax[1].text(i + (j - 1) * .26, (0 if pd.isna(r.lift) else r.lift) + .04, f'{int(r.entries)}', ha='center', fontsize=6.5)
ax[1].axhline(1, color='k', lw=.8); ax[1].set_xticks(x); ax[1].set_xticklabels(['3 months', '6 months', '12 months']); ax[1].set_ylabel('lift (labels: entries)'); ax[1].legend(frameon=False, fontsize=7); ax[1].set_title('By period of test years', fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'fig4_quota_cut.png'), dpi=200); plt.close()
# 5. property
P = pp.prices(); h = pp.hdb_rpi(); fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw=dict(width_ratios=[1.25, 1]))
for k, nm, col in (('nonlanded', 'private non-landed', A_), ('landed', 'private landed', B_)): ax[0].plot(P.index.to_timestamp(), P[k], color=col, lw=1.2, label=nm)
ax[0].plot(h.index.to_timestamp(), h, color=GD, lw=1.2, label='HDB resale'); [ax[0].axvspan(pd.Period(a).to_timestamp(), pd.Period(b).to_timestamp(), color=RD, alpha=.12, lw=0) for a, b, d, q1, q2 in N['dd']['nonlanded']]
ax[0].set_ylabel('index (2009 Q1 = 100)'); ax[0].legend(frameon=False, fontsize=7); ax[0].set_title('Price indices (shaded: falls over 10% in the non-landed index)', fontsize=8)
S = pd.DataFrame(N['prop_support']).T.drop(index=['ALL'], errors='ignore'); S = S.sort_values('lift_pre2017', ascending=False, na_position='last'); S = S[S['entries_pre2017'].astype(float) >= 60]
lab = {'momentum': 'momentum', 'rentgrowth': 'rent growth', 'rates': '2-year yield', 'vacancy': 'vacancy', 'volume': 'volume', 'pipeline': 'pipeline'}; x = np.arange(len(S)); wd = .38
ax[1].bar(x - wd / 2, S['lift_pre2017'].astype(float), wd, color=A_, label='to 2016'); ax[1].bar(x + wd / 2, S['lift_2017'].astype(float).fillna(0), wd, color=B_, label='2017 on'); ax[1].axhline(1, color='k', lw=.8)
ax[1].set_xticks(x); ax[1].set_xticklabels([lab.get(i, i) for i in S.index], fontsize=7, rotation=25); ax[1].set_ylabel('lift'); ax[1].legend(frameon=False, fontsize=7); ax[1].set_title('Private property: lift by family', fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'fig5_property.png'), dpi=200); plt.close()
# 6. replay
R = pd.DataFrame(N['retro']); R['lab'] = R['scope'] + ', ' + R['horizon'].astype(str) + (R['unit'].map({'month': 'm', 'quarter': 'q'})); R = R.sort_values('brier_all')
fig, ax = plt.subplots(figsize=(7.2, 4.0)); y = np.arange(len(R)); ax.barh(y - .2, R['brier_10y'], .38, color=B_, label='ten-year base rate'); ax.barh(y + .2, R['brier_all'], .38, color=A_, label='all-history base rate'); ax.axvline(.25, color='k', lw=1, ls='--', label='coin flip (0.250)')
ax.set_yticks(y); ax.set_yticklabels(R['lab'], fontsize=7); ax.set_xlim(.18, .36); ax.set_xlabel('Brier score (lower is better)'); ax.legend(frameon=False, fontsize=7, loc='lower right'); ax.set_title('Causal replay of the base-rate forecasts', fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'fig6_replay.png'), dpi=200); plt.close()
print('figures:', sorted(os.listdir(OUT)))
# 7. graphical abstract
thr = pd.DataFrame(N['rob_thr']); m = thr[(thr.q == 0.2) & (thr.yq == 0.2)].sort_values('tf'); P_ = pd.DataFrame(N['prop_support']).T.drop(index=['ALL'], errors='ignore'); P_ = P_[P_['entries_pre2017'].astype(float) >= 60].sort_values('lift_pre2017', ascending=False)
fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.7))
for c, col in (('A', A_), ('B', B_)): ks = sorted(N[f'lagcorr_{c}'], key=int); ax[0].plot([int(k_) for k_ in ks], [N[f'lagcorr_{c}'][k_] for k_ in ks], color=col, marker='o', ms=3, label=f'Category {c}')
ax[0].axhline(0, color='k', lw=.6); ax[0].set_xlabel('months the supply cycle leads'); ax[0].set_ylabel('correlation with the premium'); ax[0].legend(frameon=False, fontsize=6.5); ax[0].set_title('Cars: the premium lags supply', fontsize=8)
x = np.arange(3); ax[1].bar(x - .19, m['cpe'], .38, color=A_, label='after a quota cut'); ax[1].bar(x + .19, m['base'], .38, color=GR, label='base rate'); ax[1].set_xticks(x); ax[1].set_xticklabels(['3m', '6m', '12m']); ax[1].set_ylabel('chance of a top-20% rise'); ax[1].legend(frameon=False, fontsize=6.5); ax[1].set_title('Cars: one supported effect', fontsize=8)
lab = {'momentum': 'momentum', 'rentgrowth': 'rents', 'rates': 'yield', 'vacancy': 'vacancy', 'volume': 'volume', 'pipeline': 'pipeline'}; x = np.arange(len(P_))
ax[2].bar(x - .19, P_['lift_pre2017'].astype(float), .38, color=A_, label='to 2016'); ax[2].bar(x + .19, P_['lift_2017'].astype(float).fillna(0), .38, color=B_, label='2017 on'); ax[2].axhline(1, color='k', lw=.8); ax[2].set_xticks(x); ax[2].set_xticklabels([lab.get(i, i) for i in P_.index], fontsize=6.5, rotation=30); ax[2].set_ylabel('lift over base rate'); ax[2].legend(frameon=False, fontsize=6.5); ax[2].set_title('Property: nothing since 2017', fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'graphical_abstract.png'), dpi=220); plt.close(); print('graphical abstract written')
