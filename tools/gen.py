#!/usr/bin/env python3
"""Génère les SVG animés du profil (assets/).

Lancer depuis la racine du repo :
    python tools/gen.py

Sources : tools/city.jpg (bannière), tools/windows.json (fenêtres qui
scintillent), tools/icons.json (logos blancs des touches, repris du portfolio).
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
    img = base64.b64encode((TOOLS / "city.jpg").read_bytes()).decode()
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
    fs, cw = 21, 12.6  # largeur de caractère imposée via textLength
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
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="nameglow" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur in="SourceAlpha" stdDeviation="10" result="blur"/><feFlood flood-color="{RED}" flood-opacity=".55" result="col"/><feComposite in="col" in2="blur" operator="in" result="shadow"/><feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<image width="{W}" height="{H}" xlink:href="data:image/jpeg;base64,{img}" href="data:image/jpeg;base64,{img}"/>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
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


# ---------------------------------------------------------------- terminal
def terminal():
    W = 860
    lines = [
        ("cmd", "whoami"),
        ("out", "tatoune · étudiant en B2 cybersécurité @ Ynov Lyon"),
        ("cmd", "nmap -sC -sV cap.htb"),
        ("out", "21/tcp  open  ftp"),
        ("out", "22/tcp  open  ssh"),
        ("out", "80/tcp  open  http"),
        ("cmd", "wireshark 0.pcap"),
        ("ok", "identifiants FTP en clair dans la capture ✓"),
        ("cmd", "john --format=nt --wordlist=rockyou.txt hash.txt"),
        ("ok", "mot de passe retrouvé (room Blue, TryHackMe) ✓"),
        ("cmd", "go run ."),
        ("ok", "Puissance 4 en ligne · Normal, Difficile, Expert ✓"),
        ("cmd", 'git commit -m "ça marche (je crois)"'),
    ]
    fs, cw, lh = 15, 9.0, 25
    top, left = 62, 28
    H = top + lh * (len(lines) + 1) + 14
    total = 26.0
    t = 0.6
    rows = []
    for i, (kind, text) in enumerate(lines):
        y = top + lh * i + 16
        if kind == "cmd":
            prompt = f'<tspan fill="{RED}">tatoune</tspan><tspan fill="{MUTED}">@lab</tspan><tspan fill="{INK}"> $</tspan>'
            plen = len("tatoune@lab $ ")
            n = len(text)
            dur = min(0.045 * n + 0.2, 1.6)
            k, v = typing_values(n, cw, t, dur, total - 0.6, 0.0001, total)
            # ne garder que la frappe puis tenir jusqu'à la fin
            k = [x for x in k if x <= (total - 0.6) / total + 1e-9]
            v = v[: len(k)]
            k += [(total - 0.3) / total]
            v += [0]
            tx = left + plen * cw
            rows.append(
                f'<g class="row" style="animation-delay:{t:.2f}s">'
                f'<text x="{left}" y="{y}" font-family="{MONO}" font-size="{fs}" textLength="{fmt((plen-1)*cw)}" lengthAdjust="spacingAndGlyphs">{prompt}</text></g>'
                f'<clipPath id="c{i}"><rect x="{tx}" y="{y-fs}" height="{lh}" width="0">'
                f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
                f'keyTimes="{";".join(fmt(x) for x in k)}" values="{";".join(fmt(x) for x in v)}"/></rect></clipPath>'
                f'<text clip-path="url(#c{i})" x="{tx}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{INK}" '
                f'textLength="{fmt(n*cw)}" lengthAdjust="spacingAndGlyphs">{escape(text)}</text>'
            )
            t += dur + 0.45
        else:
            color = WARM if kind == "ok" else MUTED
            mark = "→ " if kind == "ok" else ""
            s = mark + text
            rows.append(
                f'<g class="row" style="animation-delay:{t:.2f}s"><text x="{left}" y="{y}" font-family="{MONO}" '
                f'font-size="{fs}" fill="{color}" textLength="{fmt(len(s)*cw)}" lengthAdjust="spacingAndGlyphs">{escape(s)}</text></g>'
            )
            t += 0.35 if kind == "out" else 0.7
    # dernière ligne : prompt + curseur
    y = top + lh * len(lines) + 16
    plen = len("tatoune@lab $ ")
    rows.append(
        f'<g class="row" style="animation-delay:{t:.2f}s"><text x="{left}" y="{y}" font-family="{MONO}" font-size="{fs}" '
        f'textLength="{fmt((plen-1)*cw)}" lengthAdjust="spacingAndGlyphs"><tspan fill="{RED}">tatoune</tspan><tspan fill="{MUTED}">@lab</tspan>'
        f'<tspan fill="{INK}"> $</tspan></text><rect class="caret" x="{left+plen*cw}" y="{y-fs+2}" width="9" height="{fs+3}" fill="{RED}"/></g>'
    )
    assert t < total - 3, t
    end = (total - 0.6) / total * 100
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Terminal de Tatoune</title>
<desc id="d">Quelques commandes que j'ai vraiment lancées : nmap sur la machine Cap (Hack The Box), Wireshark, John the Ripper sur la room Blue (TryHackMe), go run de mon Puissance 4, git commit.</desc>
<style>
text {{ white-space: pre; }}
.row {{ opacity: 0; animation: row {total}s steps(1) infinite; }}
@keyframes row {{ 0% {{ opacity: 1 }} {fmt(end)}% {{ opacity: 0 }} }}
.caret {{ animation: blink 1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ fill-opacity: 0 }} }}
@media (prefers-reduced-motion: reduce) {{ .row {{ opacity: 1; animation: none; }} .caret {{ animation: none; }} }}
</style>
<defs><linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="{RED}" stop-opacity=".22"/><stop offset="1" stop-color="{PURPLE}" stop-opacity=".12"/></linearGradient></defs>
<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="16" fill="{BG}" stroke="{RED}" stroke-opacity=".4" stroke-width="1.5"/>
<path d="M.75 16.75a16 16 0 0 1 16-16h{W-33.5}a16 16 0 0 1 16 16v23H.75z" fill="url(#bar)"/>
<circle cx="24" cy="21" r="6" fill="{RED}"/><circle cx="44" cy="21" r="6" fill="{WARM}" fill-opacity=".8"/><circle cx="64" cy="21" r="6" fill="{MUTED}" fill-opacity=".6"/>
<text x="{W/2}" y="26" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">tatoune@lab: ~</text>
{''.join(rows)}
</svg>'''
    (OUT / "terminal.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- clavier
def keys():
    icons = json.loads((TOOLS / "icons.json").read_text())
    order = [
        ("python", "Python"), ("go", "Go"), ("bash", "Bash"), ("c", "C"),
        ("html-css", "HTML / CSS"), ("javascript", "JavaScript"), ("vue", "Vue"), ("git", "Git"),
        ("linux", "Linux"), ("windows", "Windows"), ("docker", "Docker"), ("virtualization", "VirtualBox / VMware"),
        ("wireshark", "Wireshark"), ("kali", "Kali Linux"), ("burp", "Burp Suite"), ("metasploit", "Metasploit"),
    ]
    mono = [("Nmap", "Nm"), ("John / Hashcat", "JtR"), ("Active Directory", "AD"), ("Réseau TCP/IP", "IP")]
    cols, size, gap, pad = 10, 66, 12, 26
    items = [("icon", k, label) for k, label in order] + [("mono", m, label) for label, m in mono]
    rows_n = (len(items) + cols - 1) // cols
    W = pad * 2 + cols * size + (cols - 1) * gap
    H = pad * 2 + rows_n * size + (rows_n - 1) * gap + 6
    step = 0.42
    total = step * len(items) + 1.5
    rnd = random.Random(3)
    seq = list(range(len(items)))
    rnd.shuffle(seq)
    out = []
    for i, (kind, key, label) in enumerate(items):
        r, c = divmod(i, cols)
        x = pad + c * (size + gap)
        y = pad + r * (size + gap)
        delay = seq[i] * step
        if kind == "icon":
            m = re.search(r'viewBox="([^"]+)"', icons[key])
            vb = m.group(1)
            inner = re.sub(r"^<svg[^>]*>|</svg>$", "", icons[key].strip())
            inner = inner.replace("#ffffff", INK).replace("#fff", INK)
            s = size * 0.5
            face = (f'<svg x="{x+(size-s)/2}" y="{y+(size-s)/2-3}" width="{s}" height="{s}" viewBox="{vb}" '
                    f'fill="{INK}">{inner}</svg>')
        else:
            face = (f'<text x="{x+size/2}" y="{y+size/2+5}" text-anchor="middle" font-family="{SANS}" '
                    f'font-weight="800" font-size="{22 if len(key) < 3 else 19}" fill="{INK}">{key}</text>')
        out.append(
            f'<g><title>{escape(label)}</title>'
            f'<rect class="glow" x="{x-4}" y="{y+2}" width="{size+8}" height="{size+8}" rx="16" fill="{RED}" style="animation-delay:{delay:.2f}s"/>'
            f'<rect x="{x}" y="{y+5}" width="{size}" height="{size}" rx="12" fill="#050304"/>'
            f'<g class="cap" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="12" fill="url(#side)"/>'
            f'<rect x="{x+5}" y="{y+3}" width="{size-10}" height="{size-12}" rx="9" fill="url(#top)" stroke="#ffffff" stroke-opacity=".06"/>'
            f'{face}</g></g>'
        )
    p = 1 / total * 100
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Ma boîte à outils</title>
<desc id="d">Python, Go, Bash, C, HTML/CSS, JavaScript, Vue, Git, Linux, Windows, Docker, VirtualBox/VMware, Wireshark, Kali Linux, Burp Suite, Metasploit, Nmap, John/Hashcat, Active Directory, réseau TCP/IP.</desc>
<style>
.cap {{ animation: press {total:.2f}s cubic-bezier(.23,1,.32,1) infinite; }}
@keyframes press {{ 0% {{ transform: translateY(0) }} {fmt(p*0.35)}% {{ transform: translateY(4px) }} {fmt(p*1.6)}%,100% {{ transform: translateY(0) }} }}
.glow {{ opacity: 0; filter: blur(9px); animation: glow {total:.2f}s ease-out infinite; }}
@keyframes glow {{ 0% {{ opacity: 0 }} {fmt(p*0.35)}% {{ opacity: .85 }} {fmt(p*3)}%,100% {{ opacity: 0 }} }}
{REDUCED}
</style>
<defs>
<linearGradient id="side" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#2A1A1C"/><stop offset="1" stop-color="#140C0D"/></linearGradient>
<linearGradient id="top" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#2E1D1F"/><stop offset="1" stop-color="#21151A"/></linearGradient>
</defs>
<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="18" fill="{BG}" stroke="{RED}" stroke-opacity=".35" stroke-width="1.5"/>
{''.join(out)}
</svg>'''
    (OUT / "keys.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    banner()
    terminal()
    keys()
    for f in sorted(OUT.glob("*.svg")):
        print(f.name, f.stat().st_size // 1024, "Ko")
