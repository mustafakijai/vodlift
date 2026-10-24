# VodLift: Offer

*VodLift: done-for-you stream clipping, powered by Postiz.*

*Draft, October 23, 2026. Landing page: `index.html` (live on GitHub Pages, can also be deployed to postiznow.com).*

## One-liner
**You stream. We clip, caption and post everywhere.** Send us your VOD and we turn it into captioned vertical highlight clips, then schedule them to TikTok, YouTube Shorts, Instagram Reels and X through Postiz. It's a done-for-you service, so the streamer doesn't have to edit or upload anything.

## Positioning
| Option | What it does | What the streamer still has to do | Public price (checked Oct 2026) |
|---|---|---|---|
| **Opus Clip** | AI clipping. Auto-posting on paid plans | Review and fix clips, manage posting. Credits are billed per minute of source video, so long streams burn through them fast | Free (watermark), Starter $15/mo (150 min), Pro $29/mo (300 min) |
| **Eklipse** | Gaming-focused AI clipping. Publishes to TikTok and YouTube | Review, edit, publish. Instagram and X aren't covered | Premium $24.99/mo, or $179.99/yr |
| **StreamLadder** | Clip editor plus scheduler. AI clipping (ClipGPT) starts at Creator | Edit every clip. X posting only on Pro | $14.99 / $26.99 / $38.99 per month |
| Done-for-you clipping services (e.g. VodCuts) | Humans deliver MP4 clips | Post them themselves | $79/mo for 20 clips, $199/mo for 96 clips (no posting) |
| Freelance clippers | Manual edits | Brief the editor, upload, post | Roughly $2–$50 per clip depending on quality |

**Our edge:** finding the moments, editing them, and scheduling them to four platforms all happen in one place, and we do the work. The tools above are self-serve, and the services stop at the MP4 file. We run the whole loop through Postiz, where the streamer can approve or edit anything on their calendar.

**Why the prices hold up:** Starter works out to about $4 per clip including posting to four platforms. That's cheaper than most freelancers, about the same as clip-only services, and saves the streamer every hour they'd spend in a tool.

## Target customer
- Small and mid-size streamers on **Twitch, YouTube or Kick** who stream 2–6 times a week. A sweet spot is roughly 10–500 average concurrent viewers, though any active streamer qualifies.
- They already know short-form clips help them grow, but they don't have the time, editing skills or consistency to keep posting.
- Best genres: FPS and battle royale, horror, competitive, variety, and Just Chatting. Facecam streams work best.
- Where to find them: Twitch/Kick directories sorted by "Recently started" and small viewer counts, #TwitchStreamer / #SmallStreamer on X, streamer Discords, and r/Twitch "promote yourself" threads. Pitch people who already post clips inconsistently, because they've shown they want this.

## Tiers (billed monthly, cancel anytime)

| | **Starter $49/mo** | **Growth $99/mo** ⭐ | **Pro $199/mo** |
|---|---|---|---|
| Clips | **3 per week** (~12/mo) | **7 per week** (~30/mo) | **14 per week** (~60/mo, 2 a day) |
| VODs we work from | Up to 2 per week | Up to 4 per week, pulled automatically | Up to 7 per week |
| Turnaround | 48h after VOD received | 48h | **24h** |
| Platforms scheduled | TikTok, YouTube Shorts, Instagram Reels, X | Same 4 + best-time scheduling | Same 4 + Threads, Bluesky and Facebook on request |
| Format | 9:16, 15–60s, burned-in word-by-word captions, stacked / full / side-by-side layouts | + custom caption style, colors and font, on-screen hook text, zoom cuts | + priority editor, direct chat |
| Extras | Platform-specific captions and hashtags, hosted Postiz workspace | + monthly "what worked" summary | + **1 YouTube highlight compilation (5–10 min) per month** |
| Revisions | 1 per clip | 2 per clip | Unlimited (within reason) |

Unused clips don't roll over. Custom and team plans are quoted on request.

**Why these numbers:** the $49 / $99 / $199 ladder you suggested holds up. Starter is priced against VodCuts' $79 for 20 clips: fewer clips, but posting is included. Growth is the anchor tier, at about $3.30 per clip with posting. Pro sits at the same $199 as VodCuts Creator but adds 24h turnaround, more platforms and a monthly long-form video. I **capped Pro at 7 VODs a week instead of "unlimited"** because clipping-tool credits are charged per source minute. A daily 4-hour streamer is about 7,000 minutes a month, which would wipe out your margin.

**Rough delivery cost:** the included clipper costs nothing (CPU only). Optionally add one AI clipping seat (e.g. Opus Clip Pro at $29/mo for 300 min per pack, adding packs as volume grows) plus hosted Postiz for each client. You're not paying Postiz anyone else's prices, since it's your product. The rest is editing time, roughly 5–10 minutes per clip once the AI has shortlisted moments.

## The demo on the landing page
The "See it work" section is real pipeline output, not a mockup. `clipper/clip.py` was run on a 14:30 Creative Commons stream recording ("Storage Space and Smelting Trees – Ayums Ep. 5" by benrob0329, CC BY-SA 4.0, Internet Archive). It picked 3 moments automatically and exported TikTok, Reels and Shorts (1080×1920) plus X (1080×1080) versions. The page labels it as a stock-footage demo, and it shows no client results. Swap in a real client's clips (with their permission) once you have them.

## Guarantee
**"Love your first batch, or it's free."** If the streamer isn't happy with their first week of clips, we redo them. If they're still not happy, we refund the first month in full. Every plan is cancel-anytime with no contract, and the streamer keeps every MP4.

## First-week launch offer
1. **Free 3-clip sample.** No card needed. We deliver 3 finished, captioned clips from a recent VOD within 48h, plus a preview on a Postiz calendar. This is the main call to action and gets the quickest yes.
2. **Founding Streamer offer: 50% off the first month for the first 10 streamers** (Starter $24.50, Growth $49.50, Pro $99.50). The cap of 10 is real: it's about how many clients one person can deliver for well in week one. Close every sample with: *"Want these every week? Founding price is half off this month."*
3. Suggested week-one plan: send 20–30 personal pitches a day (offering the free sample), deliver samples within 48h, and follow up with the founding link. 3–5 paying streamers by day 7 is a realistic goal, not a promise.

**Outreach DM template** (personalize the first line):
> Hey {name}, caught your {game} stream, and that {specific moment} would've done numbers as a Short. I run VodLift: we turn your VODs into captioned clips and schedule them to TikTok, Shorts, Reels and X for you. Want 3 free clips from your last stream? No card, no strings: postiznow.com/{page}

## Self-serve version (waitlist, "coming soon")
**VodLift Autopilot**: paste a VOD link and AI clips, captions and schedules everything inside Postiz. The landing page collects emails now. Build it once the service has paying clients, then offer early-access pricing to the waitlist.

## Setup checklist to take payments and leads

**Payments (pick one)**
- [ ] **Stripe Payment Links** (simplest): create 3 recurring products (Starter $49, Growth $99, Pro $199 per month). Turn on "Allow promotion codes" and create a coupon such as `FOUNDING50` (50% off, once, max 10 redemptions). Alternatively, make 3 separate founding links.
- [ ] *or* **Lemon Squeezy**: it's the merchant of record and handles global sales tax/VAT. Create 3 subscription products and a 50%-off, 10-use discount.
- [ ] Paste the 3 links into `index.html`, replacing `#TODO-stripe-link-starter`, `#TODO-stripe-link-growth` and `#TODO-stripe-link-pro`.
- [ ] Set the post-payment redirect to a thank-you or onboarding form (VOD link, social handles, caption style).

**Leads**
- [ ] Free-sample form: create a Formspree, Tally or Google Form endpoint and set it as the `action` of `#applyForm` (`#TODO-apply-form-endpoint`). The JS already submits by POST and accepts a JSON response, which works with Formspree as-is. For Tally or Google Forms, embed theirs or link to it instead.
- [ ] Waitlist form: set the endpoint for `#waitlistForm` (`#TODO-waitlist-form-endpoint`), e.g. Formspree, ConvertKit, Buttondown or Mailchimp.
- [ ] Add a real contact email in place of `TODO-contact-email@postiznow.com`.
- [ ] Publish basic Terms and Privacy pages (`#TODO-terms-page`, `#TODO-privacy-page`). Include content rights, the refund policy and social-account access.
- [ ] Optional: add an OG share image (`TODO-og-image` comment in `<head>`).

**Delivery**
- [ ] Hosted Postiz workspace template for clients, with TikTok, YouTube, Instagram and X connected by the client.
- [ ] Clipping: first pass with the included `clipper/clip.py` (free, runs locally: transcribe → score → 9:16 captioned exports per platform), then an editor review. Optionally, a clipping tool account (Opus Clip / StreamLadder / Eklipse) as a backup.
- [ ] A shared folder for each client for the MP4s.
- [ ] Deploy: the site is on GitHub Pages already. To put it on postiznow.com, upload `index.html` plus the `assets/` folder (e.g. at `/streamers/`), or point a subdomain at Pages with a CNAME.
