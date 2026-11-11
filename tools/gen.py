#!/usr/bin/env python3
"""Génère la bannière animée du profil (assets/banner.svg).

Lancer depuis la racine du repo :
    python tools/gen.py

Sources : tools/city.webp (bannière agrandie 2x avec Real-ESRGAN),
tools/windows.json (fenêtres qui scintillent).
"""
import base64
import json
import random
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

# Palette tirée de la bannière
RED = "#E8352A"
RED_SOFT = "#FF6A55"
WARM = "#FFD58C"
PURPLE = "#B565FF"
INK = "#F4ECE8"
MUTED = "#A8948F"
BG = "#0A0607"

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
SANS = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

REDUCED = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"


def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def typing_values(n_chars, char_w, t_start, t_type, t_hold_end, t_erase, total):
    """Largeur d'un masque qui tape puis efface un texte (valeurs discrètes SMIL)."""
    keys, vals = [0.0], [0]
    def add(t, w):
        keys.append(t / total)
        vals.append(w)
    add(t_start, 0)
    for k in range(1, n_chars + 1):
        add(t_start + t_type * k / n_chars, k * char_w)
    add(t_hold_end, n_chars * char_w)
    for k in range(n_chars - 1, -1, -1):
        add(t_hold_end + t_erase * (n_chars - k) / n_chars, k * char_w)
    # dédoublonner les instants (keyTimes doivent croître)
    out_k, out_v = [], []
    for k, v in zip(keys, vals):
        if out_k and k <= out_k[-1]:
            out_v[-1] = v
            continue
        out_k.append(k)
        out_v.append(v)
    return out_k, out_v


# ---------------------------------------------------------------- bannière
def banner():
    W, H = 1077, 604
    img = base64.b64encode((TOOLS / "city.webp").read_bytes()).decode()
    windows = json.loads((TOOLS / "windows.json").read_text())
    rnd = random.Random(11)

    # fenêtres : la moitié s'allume plus fort, l'autre s'éteint un instant
    wins = []
    for i, (x, y) in enumerate(windows):
        dur = rnd.uniform(3.5, 9)
        delay = -rnd.uniform(0, dur)
        cls = "on" if i % 2 == 0 else "off"
        fill = WARM if cls == "on" else "#000"
        wins.append(
            f'<rect class="{cls}" x="{x-2}" y="{y-2}" width="5" height="6" rx="1" fill="{fill}" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s"/>'
        )

    # feux d'obstacle au sommet des flèches
    tips = [(555, 40, 0), (806, 100, 0.7), (352, 156, 1.3), (190, 140, 2.1), (627, 145, 1.8)]
    lights = "".join(
        f'<circle class="tip" cx="{x}" cy="{y}" r="3.2" fill="{RED_SOFT}" style="animation-delay:{d}s"/>'
        for x, y, d in tips
    )

    # phrases tapées (que des choses vraies)
    phrases = [
        "étudiant en B2 cybersécurité · Ynov Lyon",
        "labs sur TryHackMe & Hack The Box",
        "infra, réseau, Linux… et un peu de Go",
        "libéro en Nationale 3 le week-end",
    ]
    fs, cw = 18, 10.8  # largeur de caractère imposée via textLength
    x0, y0 = 46, 178
    per = 5.0
    total = per * len(phrases)
    texts = []
    last = len(phrases) - 1
    def caret_kt(i):
        a, b = fmt(i * per / total), fmt((i + 1) * per / total)
        return f"0;{b}" if i == 0 else (f"0;{a}" if i == last else f"0;{a};{b}")
    def caret_v(i):
        return "1;0" if i == 0 else ("0;1" if i == last else "0;1;0")
    for i, p in enumerate(phrases):
        n = len(p)
        start = i * per + 0.15
        k, v = typing_values(n, cw, start, 1.6, start + 3.6, 0.7, total)
        k.append(1.0)
        v.append(0)
        # chaque phrase n'a de largeur que dans sa fenêtre
        texts.append(
            f'<clipPath id="tp{i}"><rect x="{x0}" y="{y0-fs}" height="{fs+8}" width="0">'
            f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(fmt(x) for x in k)}" values="{";".join(fmt(x) for x in v)}"/></rect></clipPath>'
            f'<text clip-path="url(#tp{i})" x="{x0}" y="{y0}" font-family="{MONO}" font-size="{fs}" '
            f'fill="{INK}" textLength="{fmt(n*cw)}" lengthAdjust="spacingAndGlyphs">{escape(p)}</text>'
        )
        # caret de cette phrase : x suit la largeur
        texts.append(
            f'<rect class="caret" y="{y0-fs+3}" width="11" height="{fs+2}" fill="{RED}" x="{x0}">'
            f'<animate attributeName="x" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(fmt(x) for x in k)}" values="{";".join(fmt(x0+x+2) for x in v)}"/>'
            f'<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{caret_kt(i)}" values="{caret_v(i)}"/></rect>'
        )

    # phares sur la route du bas
    cars = "".join(
        f'<rect class="car" x="-40" y="{y}" width="34" height="2" rx="1" fill="{c}" '
        f'style="animation-duration:{d}s;animation-delay:{dl}s"/>'
        for y, c, d, dl in [(520, WARM, 9, 0), (528, RED_SOFT, 12, -5), (514, WARM, 15, -9)]
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Tatoune</title>
<desc id="d">Ville de nuit en rouge et noir. Salut, moi c'est Tatoune : étudiant en cybersécurité à Ynov Lyon.</desc>
<style>
.on {{ opacity: 0; animation: on 6s ease-in-out infinite; }}
.off {{ opacity: 0; animation: off 6s steps(1) infinite; }}
@keyframes on {{ 0%,100% {{ opacity: 0 }} 45%,55% {{ opacity: .95 }} }}
@keyframes off {{ 0%,70% {{ opacity: 0 }} 71%,88% {{ opacity: .92 }} }}
.tip {{ animation: tip 2.4s steps(1) infinite; opacity: .15; }}
@keyframes tip {{ 0% {{ opacity: 1 }} 18% {{ opacity: .15 }} }}
.beacon {{ animation: beacon 4s ease-in-out infinite; transform-origin: 556px 136px; }}
@keyframes beacon {{ 0%,100% {{ opacity: .35; transform: scale(.85) }} 50% {{ opacity: .9; transform: scale(1.15) }} }}
.car {{ animation: car 10s linear infinite; }}
@keyframes car {{ from {{ transform: translateX(0) }} to {{ transform: translateX({W+80}px) }} }}
.caret {{ animation: blink 1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ fill-opacity: 0 }} }}
.name {{ animation: rise 1.1s cubic-bezier(.23,1,.32,1) both; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(14px) }} }}
{REDUCED}
</style>
<defs>
<clipPath id="r"><rect width="{W}" height="{H}" rx="30"/></clipPath>
<radialGradient id="pg"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".9"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
<linearGradient id="sky" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".75"/><stop offset=".45" stop-color="#000" stop-opacity="0"/></linearGradient>
<radialGradient id="shade"><stop offset="0" stop-color="#000" stop-opacity=".85"/><stop offset=".6" stop-color="#000" stop-opacity=".55"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="nameglow" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur in="SourceAlpha" stdDeviation="10" result="blur"/><feFlood flood-color="{RED}" flood-opacity=".55" result="col"/><feComposite in="col" in2="blur" operator="in" result="shadow"/><feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<image width="{W}" height="{H}" href="data:image/webp;base64,{img}"/>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<ellipse cx="190" cy="110" rx="420" ry="150" fill="url(#shade)"/>
<ellipse class="beacon" cx="556" cy="136" rx="26" ry="34" fill="url(#pg)"/>
<g filter="url(#glow)">{''.join(wins)}{lights}{cars}</g>
<g class="name" filter="url(#nameglow)">
<text x="46" y="74" font-family="{MONO}" font-size="19" fill="{RED_SOFT}" letter-spacing="1">salut, moi c'est</text>
<text x="40" y="140" font-family="{SANS}" font-weight="800" font-size="74" letter-spacing="-3" fill="{INK}">Tatoune</text>
</g>
{''.join(texts)}
</g>
<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="29.5" fill="none" stroke="{RED}" stroke-opacity=".35" stroke-width="1.5"/>
</svg>'''
    (OUT / "banner.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    banner()
    for f in sorted(OUT.glob("*.svg")):
        print(f.name, f.stat().st_size // 1024, "Ko")
