"""Build index.html from src/template.html + brand symbols + the demo manifest (assets/demo/manifest.json)."""
import json, html, re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
t = (root / "src/template.html").read_text()
m = json.loads((root / "assets/demo/manifest.json").read_text())
PL = ["tiktok", "reels", "shorts", "x"]
HERO_N = m.get("hero_clip", 2)


def mmss(s):
    s = int(round(s)); return f"{s//60}:{s%60:02d}"


def vid(n, p):
    return f"assets/demo/clip{n}_{p}.mp4", f"assets/demo/clip{n}_{p}.jpg"


def why(r):
    out = []
    if r.get("loudness", 0) >= .8: out.append(f"Louder than {int(r['loudness']*100)}% of the stream")
    if r.get("speech", 0) >= .6: out.append(f"Talking {int(r['speech']*100)}% of the time")
    if r.get("hook"): out.append("Hook in the first line")
    if r.get("keywords", 0) >= 6: out.append(f"{r['keywords']} reaction words")
    return out[:3]


dur = m["source_duration"]
clips_html, segs = [], []
for c in m["clips"]:
    n = c["n"]
    src0, pos0 = vid(n, "tiktok")
    data = " ".join(f'data-{p}="{vid(n,p)[0]}" data-{p}-poster="{vid(n,p)[1]}"' for p in PL)
    quote = c["transcript"].strip()
    quote = quote[:118].rsplit(" ", 1)[0] + "…" if len(quote) > 120 else quote
    chips = "".join(f"<span>{html.escape(w)}</span>" for w in why(c["reasons"]))
    clips_html.append(f'''<div class="clip rv" data-n="{n}" {data}>
        <div class="phone"><div class="scr"><video src="{src0}" poster="{pos0}" muted loop playsinline preload="none" data-auto aria-label="Demo clip {n}: {html.escape(c['title'])}"></video><span class="demo-tag">Demo · CC stock footage</span></div></div>
        <div class="meta"><span class="t">Clip {n} · {mmss(c['start'])}–{mmss(c['end'])} · {c['duration']:.0f}s</span><b>“{html.escape(c['title'])}”</b><q>{html.escape(quote)}</q><div class="why">{chips}</div><a class="dl" href="{src0}" target="_blank" rel="noopener">Open the TikTok file ↗</a></div>
      </div>''')
    left = c["start"] / dur * 100; w = max(c["duration"] / dur * 100, 1.6)
    segs.append(f'<span class="seg" data-n="{n}" style="left:{left:.2f}%;width:{w:.2f}%" title="Clip {n}: {mmss(c["start"])}–{mmss(c["end"])}">{n}</span>')

ticks = "".join(f"<span>{mmss(dur*k/5)}</span>" for k in range(6))
hc = next(c for c in m["clips"] if c["n"] == HERO_N)
hsrc, hpos = vid(HERO_N, "tiktok")
hero = f'''<div class="phone"><div class="scr"><video src="{hsrc}" poster="{hpos}" muted loop playsinline autoplay preload="metadata" data-auto aria-label="Real demo clip made by VodLift from Creative Commons footage"></video><span class="demo-tag">Real output · CC stock footage demo</span></div></div>'''

rep = {
    "{{SYMBOLS}}": (root / "brand/symbols.svg").read_text(),
    "{{VLMARK}}": (root / "src/vlmark.svg").read_text(),
    "{{HERO_PHONE}}": hero, "{{HERO_N}}": str(HERO_N), "{{HERO_LEN}}": mmss(hc["duration"]),
    "{{CLIPS}}": "\n      ".join(clips_html), "{{TL_SEGS}}": "".join(segs), "{{TL_TICKS}}": ticks,
    "{{SRC_LEN}}": mmss(dur), "{{SRC_MIN}}": str(round(dur / 60)), "{{SEG_COUNT}}": str(m.get("segments", "169")),
    "{{SRC_TITLE}}": m["credit"]["title"], "{{SRC_AUTHOR}}": m["credit"]["author"], "{{SRC_URL}}": m["credit"]["url"],
}
for k, v in rep.items():
    t = t.replace(k, v)
left = re.findall(r"\{\{[A-Z_]+\}\}", t)
assert not left, left
(root / "index.html").write_text(t)
print("index.html", len(t), "bytes")
