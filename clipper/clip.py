#!/usr/bin/env python3
"""
clip.py: turn a long gameplay video or stream VOD into short vertical clips with burned-in captions.

Pipeline:
  1. Decode the audio with ffmpeg and transcribe it with faster-whisper (word timestamps, cached as JSON).
  2. Score candidate windows using audio energy, speech density, hook words and silence gaps.
  3. Pick the top N windows that don't overlap, snapping each one to sentence boundaries.
  4. Render a variant for each platform. Each variant has a blurred fill background and a zoomed
     gameplay panel (9:16 or 1:1). It burns in an ASS "karaoke" caption that highlights the
     current word, plus a hook title. Audio is normalised to -14 LUFS.
  5. Write H.264 MP4s with +faststart, poster JPGs, an SRT for each clip and a manifest.json.

Example:
  python clip.py input.mp4 --out out/ --clips 3 --platforms tiktok,reels,shorts,x --web
"""
import argparse, json, math, os, re, subprocess, sys, shutil
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
SR = 16000

# Platform profiles: canvas size, where the gameplay panel sits, caption/title positions and a max duration.
# TikTok, Reels and Shorts all use 1080x1920, but each UI covers a different part of the screen. Captions and
# titles are moved into each app's safe area. X gets a square cut, which takes up more of the feed
# on desktop and mobile.
PLATFORMS = {
    "tiktok": dict(w=1080, h=1920, panel_y=560, cap_y=1500, title_y=330, max_s=60,  label="TikTok"),
    "reels":  dict(w=1080, h=1920, panel_y=520, cap_y=1440, title_y=300, max_s=90,  label="Instagram Reels"),
    "shorts": dict(w=1080, h=1920, panel_y=600, cap_y=1530, title_y=360, max_s=60,  label="YouTube Shorts"),
    "x":      dict(w=1080, h=1080, panel_y=190, cap_y=930,  title_y=95,  max_s=140, label="X"),
}

HOOK_WORDS = {
    "problem": 2, "insane": 2, "insanity": 2, "crazy": 2, "annoying": 2, "why": 1, "test": 1, "finally": 2,
    "done": 1, "wow": 2, "oh": 1, "no": 1, "wait": 2, "suck": 2, "sucks": 2, "rebuild": 2, "expensive": 1,
    "actually": 1, "never": 1, "broke": 2, "broken": 2, "win": 2, "dead": 2,
    "clutch": 3, "lets": 1, "go": 1, "what": 1, "huge": 2, "first": 1, "worst": 2, "best": 2, "omg": 3,
}
HOOK_OPENERS = ("okay", "ok", "alright", "well", "so", "oh", "wait", "now")


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"command failed: {' '.join(map(str, cmd[:6]))} ...")
    return r


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    return float(d["format"]["duration"]), int(v["width"]), int(v["height"])


def load_audio(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def transcribe(audio, model_name, cache, threads):
    if cache and Path(cache).exists():
        print(f"[transcribe] using cached transcript {cache}")
        return json.load(open(cache))
    from faster_whisper import WhisperModel  # imported lazily so --help works without the package
    print(f"[transcribe] faster-whisper {model_name} int8 on CPU ({threads} threads)")
    m = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=threads)
    segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=True)
    out = {"model": model_name, "language": info.language, "duration": len(audio) / SR, "segments": []}
    for s in segs:
        out["segments"].append({"start": s.start, "end": s.end, "text": s.text.strip(),
                                "words": [{"start": w.start, "end": w.end, "word": w.word, "p": w.probability}
                                          for w in (s.words or [])]})
        print(f"  {s.start:7.1f} {s.text.strip()}")
    if cache:
        json.dump(out, open(cache, "w"), indent=1)
    return out


def energy_curve(audio, hop_s=0.25):
    hop = int(SR * hop_s)
    n = len(audio) // hop
    frames = audio[: n * hop].reshape(n, hop)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-10)
    db = 20 * np.log10(rms)
    # percentile rank, from 0 (quietest) to 1 (loudest), so scores compare across sources
    ranks = db.argsort().argsort() / max(1, n - 1)
    return ranks, hop_s


def norm_word(w):
    return re.sub(r"[^a-z']", "", w.lower()).replace("'", "")


def score_windows(tx, energy, hop_s, min_s, max_s):
    segs = [s for s in tx["segments"] if s["words"]]
    cands = []
    for i in range(len(segs)):
        start = segs[i]["start"]
        for j in range(i, len(segs)):
            end = segs[j]["end"]
            dur = end - start
            if dur > max_s:
                break
            if dur < min_s:
                continue
            words = [w for s in segs[i:j + 1] for w in s["words"]]
            speech = sum(w["end"] - w["start"] for w in words) / dur
            wps = len(words) / dur
            # longest silent gap inside the window
            gaps = [segs[k + 1]["start"] - segs[k]["end"] for k in range(i, j)]
            max_gap = max(gaps) if gaps else 0
            a, b = int(start / hop_s), int(end / hop_s)
            e = energy[a:b]
            loud = float(np.sort(e)[-max(1, len(e) // 3):].mean()) if len(e) else 0
            kw = sum(HOOK_WORDS.get(norm_word(w["word"]), 0) for w in words)
            first = segs[i]["text"].strip().lower()
            hook = 1.0 if first.startswith(HOOK_OPENERS) or any(HOOK_WORDS.get(norm_word(x), 0) >= 2 for x in first.split()[:6]) else 0.0
            prev_gap = segs[i]["start"] - segs[i - 1]["end"] if i > 0 else 9
            prev_done = i == 0 or segs[i - 1]["text"].strip().endswith((".", "!", "?"))
            starts_clean = 1.0 if (hook or prev_gap > 0.8 or prev_done) else 0.0
            ends_clean = 1.0 if segs[j]["text"].strip().endswith((".", "!", "?")) or (j + 1 < len(segs) and segs[j + 1]["start"] - end > 1.0) else 0.0
            score = (0.30 * loud + 0.25 * min(1, speech / 0.8) + 0.10 * min(1, wps / 2.5)
                     + 0.20 * min(1, kw / 8) + 0.10 * hook + 0.05 * ends_clean - 0.12 * (1 - starts_clean)
                     - 0.15 * max(0, (max_gap - 3) / 6))
            cands.append(dict(start=start, end=end, score=round(score, 4), i=i, j=j,
                              reasons=dict(loudness=round(loud, 3), speech=round(speech, 3), wps=round(wps, 2),
                                           keywords=kw, hook=hook, starts_clean=starts_clean, max_gap=round(max_gap, 2))))
    return segs, sorted(cands, key=lambda c: -c["score"])


def pick(cands, n, sep=8.0):
    chosen = []
    for c in cands:
        if all(c["end"] + sep < o["start"] or c["start"] > o["end"] + sep for o in chosen):
            chosen.append(c)
        if len(chosen) == n:
            break
    return sorted(chosen, key=lambda c: c["start"])


# ---------------------------------------------------------------- captions
def ass_time(t):
    t = max(0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def chunk_words(words, max_words=3, max_chars=16, max_pause=0.45):
    chunks, cur = [], []
    for w in words:
        txt = w["word"].strip()
        if not txt:
            continue
        if cur and (len(cur) >= max_words or len(" ".join(x["word"].strip() for x in cur + [w])) > max_chars
                    or w["start"] - cur[-1]["end"] > max_pause or cur[-1]["word"].strip()[-1:] in ".?!,"):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def clean_caption(t):
    t = re.sub(r"[,\.]+$", "", t.strip())
    t = t.replace(",,", ",")
    return t.upper()


def esc(t):
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


def build_ass(words, t0, t1, prof, title, credit, accent="&H00D32B61&", hi="&H004DE1FF&"):
    W, H = prof["w"], prof["h"]
    big = 86 if H > W else 66
    tsize = 64 if H > W else 50
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Figtree Black,{big},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Title,Figtree Black,{tsize},&H00FFFFFF,&H00FFFFFF,{accent},{accent},0,0,0,0,100,100,0,0,3,22,0,5,80,80,0,1
Style: Credit,Figtree ExtraBold,{26 if H > W else 22},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,3,10,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    dur = t1 - t0
    cx = W // 2
    # hook title: pops in, then stays
    ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(dur)},Title,,0,0,0,,{{\\pos({cx},{prof['title_y']})\\fscx80\\fscy80\\t(0,180,\\fscx100\\fscy100)}}{esc(title.upper())}")
    ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(dur)},Credit,,0,0,0,,{{\\pos({cx},{H - (70 if H > W else 40)})\\alpha&H30&}}{esc(credit)}")
    inside = [w for w in words if w["start"] >= t0 - 0.05 and w["end"] <= t1 + 0.05]
    for ch in chunk_words(inside):
        cs, ce = ch[0]["start"] - t0, ch[-1]["end"] - t0
        texts = [clean_caption(w["word"]) for w in ch]
        for k, w in enumerate(ch):
            ws = w["start"] - t0
            we = (ch[k + 1]["start"] - t0) if k + 1 < len(ch) else ce + 0.12
            parts = []
            for m, tx in enumerate(texts):
                if m == k:
                    parts.append(f"{{\\c{hi}\\fscx112\\fscy112}}{esc(tx)}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                else:
                    parts.append(esc(tx))
            pop = "\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)" if k == 0 else ""
            ev.append(f"Dialogue: 1,{ass_time(ws)},{ass_time(we)},Cap,,0,0,0,,{{\\pos({cx},{prof['cap_y']}){pop}}}{' '.join(parts)}")
    return hdr + "\n".join(ev) + "\n"


def build_srt(words, t0, t1):
    def ts(t):
        t = max(0, t); ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    inside = [w for w in words if w["start"] >= t0 - 0.05 and w["end"] <= t1 + 0.05]
    out = []
    for n, ch in enumerate(chunk_words(inside, max_words=6, max_chars=38), 1):
        out.append(f"{n}\n{ts(ch[0]['start'] - t0)} --> {ts(ch[-1]['end'] - t0)}\n{' '.join(w['word'].strip() for w in ch)}\n")
    return "\n".join(out)


def auto_title(segs, c, max_words=8):
    # use the punchiest line in the clip (most hook words, earlier lines win ties), then cut it
    # right after its last hook word so it reads like a headline instead of a sentence fragment
    best, bs = segs[c["i"]]["text"], -1
    for s in segs[c["i"]: c["j"] + 1]:
        sc = sum(HOOK_WORDS.get(norm_word(w), 0) for w in s["text"].split())
        if sc > bs:
            best, bs = s["text"], sc
    words = re.sub(r"[^\w' ]", " ", best).split()
    while words and words[0].lower() in ("okay", "ok", "so", "and", "but", "well", "yeah", "alright", "now"):
        words = words[1:]
    words = words[:max_words]
    last = max((k for k, w in enumerate(words) if HOOK_WORDS.get(norm_word(w), 0) >= 1 and norm_word(w) not in ("go", "no", "oh", "what", "why")), default=None)
    if last is not None and last >= 2:
        words = words[: last + 1]
    return " ".join(words).strip() or "Wait for it"


# ---------------------------------------------------------------- render
def render(src, src_w, src_h, t0, t1, prof, ass_path, out_path, crf, scale=1.0, fps=30):
    W, H = prof["w"], prof["h"]
    vertical = H > W
    # zoomed gameplay panel: vertical layouts crop to 4:3 so the action stays legible on a phone
    if vertical:
        cw = min(src_w, int(src_h * 4 / 3)); ch = src_h; pw = W; ph = int(W * 3 / 4)
    else:
        cw = src_w; ch = src_h; pw = W; ph = int(W * src_h / src_w)
    fs = str(FONTS).replace(":", r"\:")
    assp = str(ass_path).replace(":", r"\:")
    outw, outh = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    fc = (
        f"[0:v]fps={fps},split=2[a][b];"
        f"[a]scale=-2:{H},crop={W}:{H},gblur=sigma=38,eq=brightness=-0.18:saturation=1.25[bg];"
        f"[b]crop={cw}:{ch}:(iw-{cw})/2:(ih-{ch})/2,scale={pw}:{ph}:flags=lanczos[fg];"
        f"[bg][fg]overlay=(W-w)/2:{prof['panel_y']},"
        f"drawbox=x=0:y={prof['panel_y']}:w={W}:h={ph}:color=white@0.12:t=3,"
        f"ass='{assp}':fontsdir='{fs}',scale={outw}:{outh}:flags=lanczos,format=yuv420p[v]"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", str(src),
           "-filter_complex", fc, "-map", "[v]", "-map", "0:a:0",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-level", "4.1",
           "-g", str(fps * 2), "-c:a", "aac", "-b:a", "128k" if scale >= 1 else "96k", "-ac", "2",
           "-movflags", "+faststart", str(out_path)]
    run(cmd)


def poster(video, out_jpg, at=1.2, width=None):
    vf = ["-vf", f"scale={width}:-2"] if width else []
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", str(video), "-frames:v", "1", *vf, "-q:v", "4", str(out_jpg)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", default="out")
    ap.add_argument("--model", default="small", help="faster-whisper model: tiny, base, small or medium (int8 on CPU)")
    ap.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 4) - 1))
    ap.add_argument("--transcript", help="path for the transcript JSON cache (default: <out>/transcript.json)")
    ap.add_argument("--clips", type=int, default=3)
    ap.add_argument("--min", type=float, default=18)
    ap.add_argument("--max", type=float, default=40)
    ap.add_argument("--platforms", default="tiktok,reels,shorts,x")
    ap.add_argument("--titles", help="titles to override the auto hooks, separated by |, in clip order")
    ap.add_argument("--credit", default="", help="credit line burned into every clip (e.g. '@yourchannel')")
    ap.add_argument("--crf", type=int, default=23)
    ap.add_argument("--web", action="store_true", help="also write lightweight half-resolution copies for web embeds")
    ap.add_argument("--web-crf", type=int, default=28)
    ap.add_argument("--dry-run", action="store_true", help="only transcribe, score and print the picks")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    src = Path(a.input)
    dur, sw, sh = probe(src)
    print(f"[input] {src.name}: {dur/60:.1f} min, {sw}x{sh}")
    audio = load_audio(src)
    tx = transcribe(audio, a.model, a.transcript or out / "transcript.json", a.threads)
    if not any(s["words"] for s in tx["segments"]):
        raise SystemExit("no speech found; clip.py needs speech to pick and caption highlights")
    energy, hop = energy_curve(audio)
    segs, cands = score_windows(tx, energy, hop, a.min, a.max)
    picks = pick(cands, a.clips)
    titles = a.titles.split("|") if a.titles else []
    words = [w for s in tx["segments"] for w in s["words"]]
    manifest = {"source": src.name, "source_duration": dur, "model": tx.get("model"), "clips": []}
    for n, c in enumerate(picks, 1):
        t0 = max(0, c["start"] - 0.25); t1 = min(dur, c["end"] + 0.45)
        title = titles[n - 1] if n - 1 < len(titles) else auto_title(segs, c)
        text = " ".join(s["text"] for s in segs[c["i"]: c["j"] + 1])
        print(f"[pick {n}] {t0:7.1f}-{t1:7.1f} ({t1-t0:4.1f}s) score={c['score']} {c['reasons']}\n          title: {title}\n          text: {text[:160]}")
        entry = dict(n=n, start=round(t0, 2), end=round(t1, 2), duration=round(t1 - t0, 2), score=c["score"],
                     reasons=c["reasons"], title=title, transcript=text, files={})
        if a.dry_run:
            manifest["clips"].append(entry); continue
        (out / f"clip{n}.srt").write_text(build_srt(words, t0, t1))
        for p in [x.strip() for x in a.platforms.split(",") if x.strip()]:
            prof = PLATFORMS[p]
            e1 = min(t1, t0 + prof["max_s"])
            ass = out / f"clip{n}_{p}.ass"
            ass.write_text(build_ass(words, t0, e1, prof, title, a.credit))
            mp4 = out / f"clip{n}_{p}.mp4"
            print(f"  -> {mp4.name} {prof['w']}x{prof['h']}")
            render(src, sw, sh, t0, e1, prof, ass, mp4, a.crf)
            poster(mp4, out / f"clip{n}_{p}.jpg")
            entry["files"][p] = {"mp4": mp4.name, "poster": f"clip{n}_{p}.jpg", "size": [prof["w"], prof["h"]]}
            if a.web:
                wmp4 = out / f"clip{n}_{p}_web.mp4"
                render(src, sw, sh, t0, e1, prof, ass, wmp4, a.web_crf, scale=0.5)
                poster(wmp4, out / f"clip{n}_{p}_web.jpg")
                entry["files"][p].update(web=wmp4.name, web_poster=f"clip{n}_{p}_web.jpg")
            ass.unlink()
        manifest["clips"].append(entry)
    json.dump(manifest, open(out / "manifest.json", "w"), indent=2)
    print(f"[done] {len(picks)} clips -> {out}/manifest.json")


if __name__ == "__main__":
    main()
