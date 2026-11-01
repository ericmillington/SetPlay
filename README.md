# SetPlay

Tell it a show you saw — *"I saw Aerosmith at SPAC in 1990"* — and it finds the setlist on
[setlist.fm](https://www.setlist.fm) and builds an Apple Music playlist of the **studio
versions** of those songs, in the order they were played.

## How it works

1. **Parse** the free-text request into artist / venue / year or exact date (`lib/parseQuery.ts`).
   Venue nicknames are matched fuzzily: acronyms (`SPAC` → Saratoga Performing Arts Center),
   city names, and a small alias list (`lib/venue.ts`).
2. **Find the show** via the setlist.fm API (`lib/setlistfm.ts`). With a year, it pulls the
   artist's shows that year and ranks them by venue match; you pick the right date.
3. **Match songs** in the Apple Music catalog (`lib/appleMusic.ts`, `lib/match.ts`). Candidates are
   scored to prefer the original studio album over live, demo, remix, karaoke, tribute and
   compilation versions. Covers use the band's own studio recording if one exists, otherwise
   the original artist's. Low-confidence matches are flagged, and every song has a dropdown to
   pick a different version or untick it.
4. **Create the playlist** in your Apple Music library after you sign in with Apple (MusicKit JS).

## Setup

```bash
npm install
cp .env.example .env.local   # then fill it in (see below)
npm run dev                  # http://localhost:3000
```

### setlist.fm API key

1. Log in at setlist.fm and open <https://www.setlist.fm/settings/api>.
2. Click **Apply for an API key** and describe the app (non-commercial).
3. Put the key in `SETLISTFM_API_KEY`.

The free key is for non-commercial use and is rate-limited (about 2 requests/second).

### Apple Music (MusicKit) key

1. In <https://developer.apple.com/account/resources/identifiers/list/musicId>, create a
   **Music ID** (e.g. `music.com.yourname.setplay`).
2. In **Keys**, create a new key with **Media Services (MusicKit, ShazamKit, Apple Music Feed)**
   enabled and linked to that Music ID. Download the `.p8` file (you can only download it once).
3. Fill in `.env.local`:
   - `APPLE_TEAM_ID` — from **Membership details**
   - `APPLE_KEY_ID` — the 10-character ID of the key you just made
   - `APPLE_PRIVATE_KEY` — the contents of the `.p8` file (newlines can be written as `\n`)
   - `APPLE_STOREFRONT` — catalog country, default `us`
   - optionally `APPLE_TOKEN_ORIGIN` — e.g. `https://setplay.example.com` to restrict where the
     developer token works once deployed

Users need an Apple Music subscription to save playlists to their library.

## Scripts

- `npm run dev` — local dev server
- `npm test` — unit tests (parser, venue matching, setlist flattening, track ranking)
- `npm run typecheck`
- `npm run build && npm start` — production build

## Deploying

Any Node host that runs Next.js works (Vercel is the easiest). Set the same environment
variables there and set `APPLE_TOKEN_ORIGIN` to your site's URL.
