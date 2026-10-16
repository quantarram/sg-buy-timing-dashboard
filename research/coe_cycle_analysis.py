"""Is there a roughly decade-long cycle in the COE premium, and does the 10-year COE life explain it?
1. Periodicity: peaks and troughs of the 12-month-smoothed log premium; periodogram of the detrended log premium (linear trend in the log), Category A and B.
2. Echo: a COE lasts 10 years, so cars registered in month t reach expiry in month t+120 (renewal for 5 or 10 years is possible at the prevailing premium). Cross-correlation of de-registrations with new registrations k months earlier (k = 0..180), and of quota with new registrations 120 months earlier.
3. Pipeline: new registrations 120 months ago, as a schedule of expiries for the coming years, against current de-registrations and quota.
Caveat in the output: the premium has only about two full cycles in 24 years."""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from sgtiming import panel
Q = panel.quota_panel(); F = panel.flows()

print('1. PERIODICITY OF THE PREMIUM')
for cat in ['A', 'B']:
    lp = np.log(Q[cat]['premium']).interpolate(); sm = lp.rolling(12, center=True, min_periods=6).mean()
    # local extrema of the smoothed series with a 36-month exclusion window
    ex = []
    for i in range(36, len(sm) - 36):
        w = sm.iloc[i - 36:i + 37]
        if sm.iloc[i] == w.max(): ex.append(('peak', sm.index[i].strftime('%Y-%m'), round(float(np.exp(sm.iloc[i])))))
        if sm.iloc[i] == w.min(): ex.append(('trough', sm.index[i].strftime('%Y-%m'), round(float(np.exp(sm.iloc[i])))))
    print(f' Category {cat} extrema of the smoothed premium: {ex}')
    t = np.arange(len(lp)); b = np.polyfit(t, lp.values, 1); res = lp.values - np.polyval(b, t); res = res - res.mean()
    n = len(res); pad = 8 * n; fft = np.fft.rfft(res * np.hanning(n), pad); power = np.abs(fft) ** 2; freq = np.fft.rfftfreq(pad, d=1.0)   # cycles per month
    per = np.where(freq > 0, 1 / np.maximum(freq, 1e-9) / 12, np.inf)   # years
    m = (per >= 2) & (per <= 20); top = np.argsort(power[m])[::-1][:1]; print(f'   periodogram peak of the detrended log premium (periods 2 to 20 years): {per[m][top][0]:.1f} years; detrended series spans {n / 12:.1f} years')
    ac = pd.Series(res).autocorr
    print('   autocorrelation of the detrended log premium at lags of 2, 4, 6, 8, 10, 12 years:', [round(ac(int(12 * y)), 2) for y in (2, 4, 6, 8, 10, 12)])

print('\n2. ECHO OF THE 10-YEAR COE LIFE')
nr = (F['newreg_A'] + F['newreg_B']); dr = (F['dereg_A'] + F['dereg_B']); q = (Q['A']['quota'] + Q['B']['quota'])
d = pd.DataFrame({'nr': nr, 'dr': dr}).dropna(); res = []
for k in range(0, 181, 6):
    x = np.log(d['nr'].shift(k)); y = np.log(d['dr']); ok = x.notna() & y.notna(); res.append((k, float(np.corrcoef(x[ok], y[ok])[0, 1])))
print(' corr(log de-registrations_t, log new registrations_{t-k}) by lag k in months:'); print('  ', [(k, round(c, 2)) for k, c in res if k % 12 == 0])
best = max(res, key=lambda r: r[1]); print(f'   strongest lag in this grid: {best[0]} months (corr {best[1]:.2f})')
x = np.log(nr.shift(120)); y = np.log(q.reindex(nr.index)); ok = x.notna() & y.notna(); print(f' corr(log quota_t, log new registrations_{{t-120}}) over {ok.sum()} months: {np.corrcoef(x[ok], y[ok])[0, 1]:.2f}')
x2 = np.log(nr.shift(120).rolling(12).mean()); y2 = np.log(dr.rolling(12).mean()); ok = x2.notna() & y2.notna(); print(f' corr of 12-month means, de-registrations vs new registrations 10 years earlier: {np.corrcoef(x2[ok], y2[ok])[0, 1]:.2f} ({ok.sum()} months)')

print('\n3. EXPIRY PIPELINE (new registrations 120 months earlier, A+B, monthly average per year)')
sched = nr.copy(); sched.index = sched.index + pd.DateOffset(months=120)
for yr in range(2018, 2030):
    s = sched[sched.index.year == yr]; a = dr[dr.index.year == yr]; qq = q[q.index.year == yr]
    print(f'  {yr}: scheduled expiries (registrations of {yr - 10}) {s.mean():7.0f}/month' + (f' | actual de-registrations {a.mean():7.0f}' if len(a) else ' | (future)') + (f' | quota {qq.mean():6.0f}' if len(qq) else ''))
fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
for cat, col in (('A', 'tab:blue'), ('B', 'tab:red')): ax[0].plot(Q[cat].index, Q[cat]['premium'] / 1000, color=col, label=f'Category {cat}')
ax[0].set_ylabel('premium (S$ thousand)'); ax[0].legend(); ax[0].set_title('COE premium and the 10-year echo', fontsize=10)
ax[1].plot(nr.index, nr.rolling(6).mean(), color='tab:green', label='new registrations A+B (6-month mean)'); ax[1].plot(dr.index, dr.rolling(6).mean(), color='tab:orange', label='de-registrations A+B (6-month mean)'); ax[1].legend(fontsize=8); ax[1].set_ylabel('vehicles per month')
ax[2].plot(sched.index, sched.rolling(6).mean(), color='tab:green', label='scheduled expiries: registrations 10 years earlier'); ax[2].plot(dr.index, dr.rolling(6).mean(), color='tab:orange', label='de-registrations'); ax[2].legend(fontsize=8); ax[2].set_ylabel('vehicles per month'); ax[2].set_xlim(pd.Timestamp('2002-01-01'), pd.Timestamp('2030-01-01'))
plt.tight_layout(); plt.savefig(os.path.join(ROOT, 'research', 'coe_cycle_figure.png'), dpi=140)

print('\n4. DOES THE KNOWN-AHEAD EXPIRY SCHEDULE SAY ANYTHING ABOUT THE NEXT 24 MONTHS OF PREMIUM? (two cycles only; overlapping months)')
sch12 = np.log(sched.rolling(12).mean())               # schedule of expiries, indexed by the month the expiries fall due (known 10 years ahead)
for cat in ['A', 'B']:
    lp = np.log(Q[cat]['premium']).interpolate()
    for h in (12, 24):
        x = sch12.shift(-h) - sch12                      # change in the scheduled expiry flow over the next h months, known today
        y = lp.shift(-h) - lp
        d = pd.DataFrame({'x': x, 'y': y}).dropna(); d = d[(d.index >= '2008-01-01')]
        print(f'  Category {cat}, h={h}: corr(next-{h}m change in scheduled expiries, next-{h}m change in premium) = {d.x.corr(d.y):+.2f} over {len(d)} months (about {len(d)/h:.1f} independent windows)')
        # sign hit rate: when the schedule says supply will rise, does the premium fall?
        up = d[d.x > 0.15]; dn = d[d.x < -0.15]
        print(f'     schedule rising by >15%: {len(up)} months, premium fell in {np.mean(up.y < 0):.2f}; schedule falling by >15%: {len(dn)} months, premium rose in {np.mean(dn.y > 0):.2f}')
latest = sched.rolling(12).mean()
print('\n  scheduled expiries, 12-month mean (vehicles per month): mid-2026', round(float(latest['2026-08-01'])), '| 12 months ahead (Aug 2027)', round(float(latest['2027-08-01'])), '| 24 months ahead (Aug 2028)', round(float(latest['2028-08-01'])), '| actual de-registrations, 12-month mean now', round(float(dr.rolling(12).mean().iloc[-1])))

print('\n5. LAG STRUCTURE: detrended log premium against the supply cycle (12-month mean de-registrations, A+B) k months earlier')
dr12 = np.log(dr.rolling(12).mean())
for cat in ['A', 'B']:
    lp = np.log(Q[cat]['premium']).interpolate(); t = np.arange(len(lp)); res = pd.Series(lp.values - np.polyval(np.polyfit(t, lp.values, 1), t), index=lp.index)
    out = []
    for k in range(0, 61, 6):
        d = pd.DataFrame({'p': res, 's': dr12.shift(k)}).dropna(); out.append((k, round(d.p.corr(d.s), 2)))
    best = min(out, key=lambda r: r[1]); print(f'  Category {cat}: corr by lag k (months) {out}; most negative at k = {best[0]} ({best[1]})')
    for lab, a, b in (('2002-2013', '2002-01-01', '2013-12-31'), ('2014-2026', '2014-01-01', '2026-09-30')):
        dd = pd.DataFrame({'p': res, 's': dr12.shift(18)})[a:b].dropna(); print(f'     lag 18 months, {lab}: {dd.p.corr(dd.s):+.2f} ({len(dd)} months)')
