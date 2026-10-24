# VodLift clipper

`clip.py` turns a long gameplay video or stream VOD into short, captioned clips for TikTok, Instagram Reels, YouTube Shorts and X. It's the first-pass pipeline behind the demo on the VodLift landing page.

Everything runs locally on a CPU. There are no API keys and nothing is uploaded.

## What it does

1. **Transcribes** the audio with [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (int8 on CPU, with word timestamps). The transcript is cached as JSON, so re-runs are instant.
2. **Scores** every candidate window (18–40s by default, starting and ending on sentence boundaries) on:
   - loudness: how much of the window is in the loudest third of the stream (30%)
   - how much of the window is speech (25%)
   - talking pace in words per second (10%)
   - reaction and "something happened" words (20%)
   - a hook in the first line (10%)
   - ending on a finished sentence (5%)
   - a penalty for dead air over 3s, and for starting mid-sentence
3. **Picks** the top N windows that don't overlap, spaced at least 8s apart.
4. **Renders** each clip for each platform:
   - a blurred, darkened fill of the frame behind a framed gameplay panel (4:3 crop for vertical, full 16:9 for X)
   - a hook title in a purple box at the top
   - word-by-word "karaoke" captions in Figtree Black with the current word highlighted
   - an optional credit line
   - audio normalized to −14 LUFS
5. **Exports** H.264 High-profile MP4s with `+faststart` (they start playing before the download finishes), plus:
   - a poster JPG for each video
   - an `.srt` for each clip, for platforms that want separate captions
   - a `manifest.json` with timings, scores and the reasons each clip was picked

### Platform profiles

| Profile | Canvas | Max length | Notes |
|---|---|---|---|
| `tiktok` | 1080×1920 | 60s | Captions kept above the caption and description area |
| `reels` | 1080×1920 | 90s | Slightly higher caption line, because the Reels UI covers more of the bottom |
| `shorts` | 1080×1920 | 60s | Title pushed lower, below the Shorts top bar |
| `x` | 1080×1080 | 140s | Square, which fills more of the feed on desktop and mobile |

You can change the positions in the `PLATFORMS` dict at the top of `clip.py`.

## Install

```bash
# ffmpeg needs libass (for burned-in subtitles) and libx264; most distro / Homebrew builds have both
sudo apt install ffmpeg            # or: brew install ffmpeg
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

The Figtree fonts are in `fonts/` (SIL Open Font License, see `fonts/OFL.txt`). Nothing needs to be installed system-wide.

## Use

```bash
# see what it would pick, without rendering anything
python clip.py my_vod.mp4 --out out --dry-run

# 3 clips, all four platforms, plus half-size copies for a website
python clip.py my_vod.mp4 --out out --clips 3 --platforms tiktok,reels,shorts,x --web --credit "@yourchannel"

# write your own hook titles (in clip order) instead of the automatic ones
python clip.py my_vod.mp4 --out out --titles "1 HP clutch|Chat called it|This boss is unfair"
```

| Option | Default | |
|---|---|---|
| `--model` | `small` | faster-whisper model: `tiny`, `base`, `small` or `medium`. `small` int8 needs about 1 GB of RAM. |
| `--threads` | cores − 1 | CPU threads for transcription |
| `--transcript` | `<out>/transcript.json` | Transcript cache path |
| `--clips` | 3 | Number of clips |
| `--min` / `--max` | 18 / 40 | Clip length window, in seconds |
| `--platforms` | `tiktok,reels,shorts,x` | Comma-separated profiles |
| `--titles` | auto | Hook titles separated by `\|` |
| `--credit` | none | Small credit line burned into every clip |
| `--crf` | 23 | x264 quality for the full-size files (lower is better and bigger) |
| `--web` / `--web-crf` | off / 28 | Also write half-resolution copies (`*_web.mp4`) |

**Speed.** On an 8-core CPU, the 14.5-minute demo VOD took about 70s to transcribe with `small` int8. Rendering takes roughly 15–25s per clip per platform.

## Notes and limits

- **Speech required.** The picker relies on speech. Clips from gameplay with no commentary won't score well (it exits with a message if it finds no speech at all).
- **English hook words.** The hook-word list is English and tuned for gaming streams. Edit `HOOK_WORDS` for your language or genre.
- **Fixed framing.** The vertical crop is a fixed center 4:3 panel. There is no face-cam detection or auto-reframe. In the paid service, an editor picks the layout (stacked facecam, full gameplay and so on).
- **PyAV note.** Some PyAV / faster-whisper version pairs fail inside `decode_audio` (`TypeError: ... metadata_errors`). `clip.py` avoids this by decoding the audio with ffmpeg itself and passing a NumPy array to Whisper.
- **Rights.** Only clip content you own or have permission to use. The demo on the landing page was made from a CC BY-SA 4.0 stream recording (see `../CREDITS.md`), so those demo clips are CC BY-SA 4.0 too.

## License

The code is MIT licensed (see `../LICENSE`). The fonts are covered by the SIL OFL.
