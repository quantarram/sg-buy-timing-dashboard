"""Recomputes every number quoted in the paper from the committed data and research outputs, and writes paper/numbers.json. python paper/paper_numbers.py"""
import json, os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import panel, property_panel as pp, property_state as ps
N = {}
Q = panel.quota_panel(); F = panel.flows(); R = panel.rates(); idx = Q['A'].index
N['months'] = len(idx); N['start'] = idx[0].strftime('%B %Y'); N['end'] = idx[-1].strftime('%B %Y')
for c in 'AB':
    p = Q[c]['premium'].dropna(); N[f'prem_{c}_last'] = float(p.iloc[-1]); N[f'prem_{c}_max'] = float(p.max()); N[f'prem_{c}_max_date'] = p.idxmax().strftime('%B %Y'); N[f'prem_{c}_min'] = float(p.min()); N[f'prem_{c}_min_date'] = p.idxmin().strftime('%B %Y'); N[f'prem_{c}_first'] = float(p.iloc[0])
# ---- cycle
for c in 'AB':
    lp = np.log(Q[c]['premium']).interpolate(); sm = lp.rolling(12, center=True, min_periods=6).mean(); ex = []
    for i in range(36, len(sm) - 36):
        w = sm.iloc[i - 36:i + 37]
        if sm.iloc[i] == w.max(): ex.append(('peak', sm.index[i].strftime('%Y-%m'), float(np.exp(sm.iloc[i]))))
        if sm.iloc[i] == w.min(): ex.append(('trough', sm.index[i].strftime('%Y-%m'), float(np.exp(sm.iloc[i]))))
    N[f'extrema_{c}'] = ex
    t = np.arange(len(lp)); res = lp.values - np.polyval(np.polyfit(t, lp.values, 1), t); res = res - res.mean(); n = len(res); pad = 8 * n
    pw = np.abs(np.fft.rfft(res * np.hanning(n), pad)) ** 2; fr = np.fft.rfftfreq(pad, d=1.0); per = np.where(fr > 0, 1 / np.maximum(fr, 1e-9) / 12, np.inf); m = (per >= 2) & (per <= 20)
    N[f'period_{c}'] = float(per[m][np.argmax(pw[m])]); N['span_years'] = n / 12; ac = pd.Series(res).autocorr; N[f'ac10_{c}'] = float(ac(120)); N[f'ac12_{c}'] = float(ac(144))
nr = F['newreg_A'] + F['newreg_B']; dr = F['dereg_A'] + F['dereg_B']; q = Q['A']['quota'] + Q['B']['quota']; sched = nr.shift(120)
d_ = pd.DataFrame({'nr': nr, 'dr': dr}).dropna(); N['corr_dereg_newreg_lag0'] = float(np.corrcoef(np.log(d_.nr), np.log(d_.dr))[0, 1])
x = np.log(nr.shift(120)); y = np.log(dr); ok = x.notna() & y.notna(); N['corr_dereg_newreg_lag120'] = float(np.corrcoef(x[ok], y[ok])[0, 1])
for a, b in (('2000-01', '2009-12'), ('2010-01', '2017-12'), ('2018-01', '2026-08')):
    xx = np.log(sched.rolling(12).mean())[a:b]; yy = np.log(dr.rolling(12).mean())[a:b]; ok = xx.notna() & yy.notna(); N[f'corr_sched_dereg_{a[:4]}_{b[:4]}'] = float(np.corrcoef(xx[ok], yy[ok])[0, 1])
xx = np.log(dr.rolling(12).mean()); yy = np.log(q.reindex(dr.index).rolling(12).mean()); ok = xx.notna() & yy.notna(); N['corr_dereg_quota'] = float(np.corrcoef(xx[ok], yy[ok])[0, 1])
dr12 = np.log(dr.rolling(12).mean())
for c in 'AB':
    lp = np.log(Q[c]['premium']).interpolate(); t = np.arange(len(lp)); res = pd.Series(lp.values - np.polyval(np.polyfit(t, lp.values, 1), t), index=lp.index); cors = {}
    for k in range(0, 61, 6): dd = pd.DataFrame({'p': res, 's': dr12.shift(k)}).dropna(); cors[k] = float(dd.p.corr(dd.s))
    N[f'lagcorr_{c}'] = cors; kb = min(cors, key=cors.get); N[f'lagbest_{c}'] = [kb, cors[kb]]
    for lab, a, b in (('h1', '2002-01-01', '2013-12-31'), ('h2', '2014-01-01', '2026-09-30')):
        dd = pd.DataFrame({'p': res, 's': dr12.shift(18)})[a:b].dropna(); N[f'lag18_{c}_{lab}'] = float(dd.p.corr(dd.s))
schedf = nr.copy(); schedf.index = nr.index + pd.DateOffset(months=120); sr = schedf.rolling(12).mean()
N['sched_now'] = float(sr['2026-08-01']); N['sched_1y'] = float(sr['2027-08-01']); N['sched_2y'] = float(sr['2028-08-01']); N['dereg12_now'] = float(dr.rolling(12).mean().iloc[-1])
# ---- walk-forward
S = pd.read_csv(os.path.join(ROOT, 'research', 'coe_walkforward_summary.csv')).set_index('group'); N['coe_wf'] = {k: dict(zip(S.columns, v)) for k, v in zip(S.index, S.values) if k in ('ALL admitted',) or k.startswith('fam=') or k.startswith('tf=') or k.startswith('q=') or k.startswith('cat=')}
N['coe_support'] = pd.read_csv(os.path.join(ROOT, 'research', 'coe_family_support.csv')).set_index('family').to_dict('index')
N['coe_year_lift'] = {k[5:]: float(S.loc[k, 'lift']) for k in S.index if k.startswith('year=')}
N['coe_year_entries'] = {k[5:]: int(S.loc[k, 'entries']) for k in S.index if k.startswith('year=')}
N['rob_thr'] = pd.read_csv(os.path.join(ROOT, 'research', 'coe_robustness_thresholds.csv')).to_dict('records'); N['rob_sub'] = pd.read_csv(os.path.join(ROOT, 'research', 'coe_robustness_subperiods.csv')).to_dict('records'); N['rob_reg'] = pd.read_csv(os.path.join(ROOT, 'research', 'coe_robustness_regression.csv')).to_dict('records')
# ---- property
P = pp.prices(); N['ppi_start'] = str(P.index[0]); N['ppi_end'] = str(P.index[-1])
PS = pd.read_csv(os.path.join(ROOT, 'research', 'property_walkforward_summary.csv')).set_index('group'); N['prop_all'] = dict(PS.loc['ALL admitted'])
N['prop_support'] = pd.read_csv(os.path.join(ROOT, 'research', 'property_family_support.csv')).set_index('family').to_dict('index')
N['hdb_support'] = pd.read_csv(os.path.join(ROOT, 'research', 'hdb_rpi_family_support.csv')).set_index('family').to_dict('index'); N['hdb_state'] = json.load(open(os.path.join(ROOT, 'research', 'hdb_rpi_state.json')))
N['base'] = ps.base_rates(P); N['dd'] = {t: ps.drawdowns(P[t]) for t in ('nonlanded', 'landed')}
N['ind'] = ps.indicators(P, pp.rents(), pp.transactions(), pp.new_sales(), pp.supply())[0]
# ---- ledger replay
L = pd.read_csv(os.path.join(ROOT, 'data', 'ledger', 'retrospective.csv')); N['retro'] = L.to_dict('records'); N['n_forecasts'] = len(pd.read_csv(os.path.join(ROOT, 'data', 'ledger', 'forecasts.csv')))
json.dump(N, open(os.path.join(ROOT, 'paper', 'numbers.json'), 'w'), indent=1, default=lambda o: (float(o) if isinstance(o, (np.floating,)) else (int(o) if isinstance(o, np.integer) else str(o))))
print('numbers written;', len(N), 'keys'); print({k: N[k] for k in ('months','start','end','span_years','period_A','period_B','corr_sched_dereg_2018_2026','corr_dereg_quota','lagbest_A','lagbest_B','sched_now','sched_1y','dereg12_now')})
