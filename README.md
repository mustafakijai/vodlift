# VodLift

**You stream. We clip & post everywhere.** VodLift is a done-for-you clipping service for Twitch, YouTube and Kick streamers. We take your VOD, find the best moments, cut them into captioned vertical clips and schedule them to TikTok, YouTube Shorts, Instagram Reels and X. It's *powered by [Postiz](https://postiz.com)*.

**Live site:** https://mustafakijai.github.io/vodlift/

![Desktop preview](preview-desktop.png)

## What's in this repo

| Path | What it is |
|---|---|
| `index.html` | The landing page: one static file, no build step needed to host it |
| `assets/img/` | Licensed stock photos (Pexels), optimized to WebP |
| `assets/demo/` | **Real demo output:** 3 clips × 4 platforms made from a CC BY-SA stream recording, plus posters, SRTs and `manifest.json` |
| `assets/brand/` | VodLift mark / favicon |
| `clipper/` | `clip.py`, the reusable long-video → short-clips pipeline (faster-whisper + ffmpeg). See [clipper/README.md](clipper/README.md) |
| `src/` | `template.html` + `build.py` (rebuilds `index.html` from the demo manifest), `shoot.py` (screenshots) |
| `offer.md` | The offer: positioning, tiers, guarantee, launch plan and setup checklist |
| `CREDITS.md` | Every third-party asset, with its license |

## The demo is real, but it isn't a client

We ran the "See it work" section's pipeline end to end on a 14:30 Minetest stream by **benrob0329** (CC BY-SA 4.0, Internet Archive):

1. transcribe it
2. score every window
3. pick the top 3
4. reframe and caption them
5. export per platform

It's clearly labeled on the page as a stock-footage demo. It doesn't use any client, real customer stats or testimonials.

Rebuild the clips yourself:

```bash
pip install -r clipper/requirements.txt
python clipper/clip.py your_vod.mp4 --out out --clips 3 --web
```

To use new clips on the page, copy `out/clip{n}_{platform}_web.mp4/.jpg` to `assets/demo/clip{n}_{platform}.mp4/.jpg`, copy `out/manifest.json` there too and add a `credit` block. Then run `python3 src/build.py`.

## Before taking money (TODOs left on purpose)

Search `index.html` (or `src/template.html`) for `TODO`:

- `#TODO-stripe-link-starter`, `#TODO-stripe-link-growth`, `#TODO-stripe-link-pro`: Stripe Payment Links
- `#TODO-apply-form-endpoint`, `#TODO-waitlist-form-endpoint`: form endpoints (Formspree etc.)
- `TODO-contact-email@postiznow.com`: real contact email
- `#TODO-terms-page`, `#TODO-privacy-page`: legal pages
- `TODO-og-image`: social share image

`offer.md` has the full checklist.

## Hosting

GitHub Pages serves the site from the `main` branch root. To host it on your own domain (e.g. postiznow.com), upload `index.html` together with `assets/`.

## License

The code is MIT (`LICENSE`). The demo clips are CC BY-SA 4.0 and the photos are under the Pexels License. See `CREDITS.md`.
