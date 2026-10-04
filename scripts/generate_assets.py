#!/usr/bin/env python3
"""Generate the SVG assets used by README.md, with no third-party services.

Static parts (header, footer, tech badges, contact pills) are drawn from the
data below. The stats cards are a snapshot of public data from api.github.com,
fetched when this script runs. Re-run it to refresh them:

    python scripts/generate_assets.py

Set GITHUB_TOKEN to avoid the unauthenticated API rate limit (optional).
Only the Python standard library is used.
"""
import json
import math
import os
import urllib.request
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

USER = "jpablodrexler"
NAME = "Juan Pablo Drexler"
TITLE = "Senior Software Architect · Technical Leader"
SUBTITLE = "AI Developer / Full Stack Developer · DevOps"
ASSETS = Path(__file__).resolve().parent.parent / "assets"

BLUE, PURPLE = "#0e75b6", "#512BD4"
FONT = "'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif"

# (label, colour): brand colours for tools, NEUTRAL for concepts and practices
NEUTRAL = "#57606a"
TECH_DEEP = [
    ("Java & Spring", "#6DB33F"), ("C#", "#239120"), (".NET", "#512BD4"),
    ("ASP.NET Core", "#512BD4"), ("Angular", "#DD0031"),
    ("Microservices", NEUTRAL), ("Event-Driven Architecture", NEUTRAL),
    ("SOA", NEUTRAL), ("Design Patterns", NEUTRAL), ("SOLID", NEUTRAL),
    ("TDD & Unit Testing", NEUTRAL),
    ("DevOps", NEUTRAL), ("Azure", "#0078D4"), ("AWS", "#232F3E"), ("MS SQL Server", "#CC2927"),
    ("PostgreSQL", "#4169E1"), ("Azure DevOps", "#0078D7"),
    ("GitHub Actions", "#2088FF"), ("Git", "#F05032"),
]
TECH_WORKING = [
    ("Claude Code", "#D97757"), ("Skills", NEUTRAL),
    ("Spec-Driven Development", NEUTRAL), ("MCP", NEUTRAL),
    ("Docker", "#2496ED"), ("Kubernetes", "#326CE5"), ("Terraform", "#7B42BC"),
    ("Redis", "#DC382D"), ("MongoDB", "#47A248"), ("Kafka", "#231F20"),
    ("Elasticsearch", "#005571"), ("GraphQL", "#E10098"),
    ("Google Cloud", "#4285F4"), ("GitHub Copilot", "#24292f"), ("Ollama", "#3a3a3a"),
    ("Entity Framework", "#512BD4"), ("WCF", "#512BD4"), ("WPF", "#512BD4"),
]
CONTACT = [
    ("linkedin", "LinkedIn", "#0A66C2"),
]
LANG_COLORS = {
    "Java": "#b07219", "TypeScript": "#3178c6", "C#": "#178600",
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "Shell": "#89e051",
    "SCSS": "#c6538c", "Python": "#3572A5", "Dockerfile": "#384d54",
    "Batchfile": "#C1F12E",
}
THEMES = {
    "light": dict(bg="#ffffff", border="#d0d7de", title=BLUE, text="#24292f", muted="#57606a", track="#eaeef2"),
    "dark": dict(bg="#0d1117", border="#30363d", title="#58a6ff", text="#e6edf3", muted="#8b949e", track="#21262d"),
}


def write(name, svg):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print("wrote", name)


def text_width(s, px):
    # Rough width estimate for a proportional sans-serif font.
    return len(s) * px * 0.58


# ---------------------------------------------------------------- header/footer
def wave(w, h, base, amp, phase, opacity):
    pts = []
    for i in range(0, w + 20, 20):
        y = base + amp * math.sin(i / w * 2 * math.pi + phase)
        pts.append(f"{i},{y:.1f}")
    return (f'<polygon points="0,{h} ' + " ".join(pts) + f' {w},{h}" fill="#fff" fill-opacity="{opacity}"/>')


def header():
    w, h = 1000, 215
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{escape(NAME)} - {escape(TITLE)} - {escape(SUBTITLE)}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient></defs>
  <rect width="{w}" height="{h}" fill="url(#g)"/>
  {wave(w, h, 175, 10, 0.0, 0.10)}
  {wave(w, h, 190, 8, 2.0, 0.14)}
  {wave(w, h, 203, 6, 4.0, 0.22)}
  <text x="{w/2}" y="78" text-anchor="middle" font-family="{FONT}" font-size="46" font-weight="700" fill="#fff">{escape(NAME)}</text>
  <text x="{w/2}" y="114" text-anchor="middle" font-family="{FONT}" font-size="21" fill="#fff" fill-opacity="0.95">{escape(TITLE)}</text>
  <text x="{w/2}" y="144" text-anchor="middle" font-family="{FONT}" font-size="17" fill="#fff" fill-opacity="0.85">{escape(SUBTITLE)}</text>
</svg>
"""


def footer():
    w, h = 1000, 90
    top = " ".join(f"{i},{34 + 10 * math.sin(i / w * 2 * math.pi + 1):.1f}" for i in range(0, w + 20, 20))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient></defs>
  <polygon points="0,{h} {top} {w},{h}" fill="url(#g)"/>
</svg>
"""


# ---------------------------------------------------------------------- pills
def pill(x, y, label, color, h=30, px=13):
    w = text_width(label, px) + 28
    return w, (
        f'<g><rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{color}" stroke="#ffffff" stroke-opacity="0.18"/>'
        f'<text x="{x + w/2:.1f}" y="{y + h/2 + px*0.35:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{px}" '
        f'font-weight="600" fill="#fff">{escape(label)}</text></g>'
    )


def badges(items, max_w=900, gap=8, row_h=38):
    x = y = 0
    rows, parts, widest = 1, [], 0
    for label, color in items:
        w, svg = pill(0, 0, label, color)
        if x and x + w > max_w:
            x, y, rows = 0, y + row_h, rows + 1
        parts.append(pill(x, y, label, color)[1])
        x += w + gap
        widest = max(widest, x - gap)
    h = rows * row_h - (row_h - 30)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {widest:.0f} {h}" width="{widest:.0f}" height="{h}" '
        f'role="img" aria-label="{escape(", ".join(l for l, _ in items))}">' + "".join(parts) + "</svg>\n"
    )


def contact_pill(label, color):
    w, body = pill(0, 0, label, color, h=36, px=15)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} 36" width="{w:.0f}" height="36" role="img" '
        f'aria-label="{escape(label)}">{body}</svg>\n'
    )


# ----------------------------------------------------------------- stats cards
def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"User-Agent": "profile-readme-generator"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_stats():
    user = api(f"/users/{USER}")
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner")]
    own = [r for r in repos if not r["fork"]]
    langs = {}
    for r in own:
        for lang, n in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[lang] = langs.get(lang, 0) + n
    return dict(
        repos=user["public_repos"],
        followers=user["followers"],
        stars=sum(r["stargazers_count"] for r in own),
        forks=sum(r["forks_count"] for r in own),
        since=user["created_at"][:4],
        langs=langs,
    )


def card_frame(t, w, h, title, inner):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(title)}">
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="8" fill="{t['bg']}" stroke="{t['border']}"/>
  <text x="24" y="34" font-family="{FONT}" font-size="17" font-weight="700" fill="{t['title']}">{escape(title)}</text>
  {inner}
  <text x="{w-16}" y="{h-12}" text-anchor="end" font-family="{FONT}" font-size="10" fill="{t['muted']}">snapshot {date.today().isoformat()}</text>
</svg>
"""


def stats_card(t, s):
    rows = [("Public repositories", s["repos"]), ("Stars earned", s["stars"]),
            ("Forks", s["forks"]), ("Followers", s["followers"]), ("On GitHub since", s["since"])]
    out = []
    for i, (label, value) in enumerate(rows):
        y = 66 + i * 26
        out.append(
            f'<text x="24" y="{y}" font-family="{FONT}" font-size="14" fill="{t["muted"]}">{escape(label)}</text>'
            f'<text x="276" y="{y}" text-anchor="end" font-family="{FONT}" font-size="14" font-weight="700" fill="{t["text"]}">{escape(str(value))}</text>'
        )
    return card_frame(t, 300, 210, "GitHub stats", "".join(out))


def langs_card(t, s, top=6):
    total = sum(s["langs"].values()) or 1
    items = sorted(s["langs"].items(), key=lambda kv: -kv[1])[:top]
    shown = sum(n for _, n in items)
    bar_w, x, bar, legend = 252, 24, [], []
    for i, (lang, n) in enumerate(items):
        w = bar_w * n / shown
        bar.append(f'<rect x="{x:.1f}" y="50" width="{w:.1f}" height="10" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>')
        x += w
        col, row = i % 2, i // 2
        lx, ly = 24 + col * 130, 88 + row * 24
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-family="{FONT}" font-size="12" fill="{t["text"]}">{escape(lang)} '
            f'<tspan fill="{t["muted"]}">{100 * n / total:.1f}%</tspan></text>'
        )
    inner = (f'<clipPath id="c"><rect x="24" y="50" width="{bar_w}" height="10" rx="5"/></clipPath>'
             f'<g clip-path="url(#c)">{"".join(bar)}</g>{"".join(legend)}')
    return card_frame(t, 300, 210, "Top languages", inner)


def main():
    write("header.svg", header())
    write("footer.svg", footer())
    write("tech-deep.svg", badges(TECH_DEEP))
    write("tech-working.svg", badges(TECH_WORKING))
    for key, label, color in CONTACT:
        write(f"contact-{key}.svg", contact_pill(label, color))
    s = fetch_stats()
    for name, t in THEMES.items():
        write(f"stats-{name}.svg", stats_card(t, s))
        write(f"top-langs-{name}.svg", langs_card(t, s))


if __name__ == "__main__":
    main()
