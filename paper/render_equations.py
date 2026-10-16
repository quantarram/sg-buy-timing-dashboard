"""Renders the paper's display equations with matplotlib mathtext + STIX (real typeset math, no LaTeX install), as SVG in paper/eq/."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["mathtext.fontset"] = "stix"; plt.rcParams["font.family"] = "STIXGeneral"; plt.rcParams["svg.fonttype"] = "path"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eq"); os.makedirs(OUT, exist_ok=True)


def render(name, lines, fontsize=13.0):
    fig = plt.figure(figsize=(0.1, 0.1)); rend = fig.canvas.get_renderer(); hs, mw = [], 0
    for ln in lines:
        t = fig.text(0, 0, ln, fontsize=fontsize); bb = t.get_window_extent(renderer=rend); mw = max(mw, bb.width); hs.append(bb.height * 1.35)
    plt.close(fig); th = sum(hs); fig = plt.figure(figsize=(mw * 1.06 / 72, th / 72)); y = th
    for ln, h in zip(lines, hs):
        y -= h; fig.text(0.0, (y + h / 2) / th, ln, fontsize=fontsize, va="center", ha="left")
    fig.savefig(os.path.join(OUT, name + ".svg"), transparent=True); plt.close(fig)


render("eq1_cpe", [r"$\mathrm{CPE}(q_X)=\Pr\!\left(Y_{t,\tau_f}\in\mathcal{T}_Y\;\mid\;X_{t,\tau_p}\in\mathcal{T}_X(q_X)\right),\qquad L=\dfrac{\mathrm{CPE}(q_X)}{b}$"])
render("eq2_base", [r"$b=\dfrac{1}{n}\sum_{i=1}^{n}\bar{e}_{m(i)}$"])
render("eq3_admit", [r"$\mathcal{A}_y=\left\{c:\;L_c^{(<y)}\geq 1.5,\;\;n_c^{(<y)}\geq 20,\;\;\mathrm{ep}_c^{(<y)}\geq 4\right\}$"])
render("eq4_echo", [r"$E_t=N_{t-120},\qquad S_t=\dfrac{1}{12}\sum_{j=0}^{11}E_{t-j}$"])
render("eq5_reg", [r"$\ln\dfrac{P_{t+12}}{P_t}=\alpha+\beta^{-}\min\!\left(\Delta_6\ln Q_t,\,0\right)+\beta^{+}\max\!\left(\Delta_6\ln Q_t,\,0\right)+\varepsilon_t$"])
render("eq6_brier", [r"$B=\dfrac{1}{N}\sum_{i=1}^{N}\left(p_i-o_i\right)^2$"])
render("eq7_support", [r"$L_f^{\mathrm{all}}\geq 1.4,\qquad L_f^{\geq 2017}\geq 1.4,\qquad n_f\geq 100$"])
print("rendered", sorted(os.listdir(OUT)))
