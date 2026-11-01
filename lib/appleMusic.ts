import { SignJWT, importPKCS8 } from "jose";
import type { SetlistSong, TrackCandidate, TrackMatch } from "./types";
import { HIGH_CONFIDENCE, MIN_ACCEPTABLE, type RawCandidate, rankCandidates } from "./match";

const API = "https://api.music.apple.com/v1";

export class AppleMusicError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

let cached: { token: string; expires: number } | undefined;

/**
 * Signs an Apple Music developer token (ES256 JWT) from the MusicKit key in the environment.
 * Developer tokens are designed to be handed to MusicKit JS in the browser.
 */
export async function getDeveloperToken(): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (cached && cached.expires - now > 600) return cached.token;

  const teamId = process.env.APPLE_TEAM_ID;
  const keyId = process.env.APPLE_KEY_ID;
  const rawKey = process.env.APPLE_PRIVATE_KEY;
  if (!teamId || !keyId || !rawKey) {
    throw new AppleMusicError("Apple Music isn't configured: set APPLE_TEAM_ID, APPLE_KEY_ID and APPLE_PRIVATE_KEY", 500);
  }
  const pem = rawKey.includes("\\n") ? rawKey.replace(/\\n/g, "\n") : rawKey;
  const key = await importPKCS8(pem.trim(), "ES256");

  const ttl = 60 * 60 * 12; // 12 hours (Apple allows up to 6 months)
  const payload: Record<string, unknown> = {};
  if (process.env.APPLE_TOKEN_ORIGIN) payload.origin = process.env.APPLE_TOKEN_ORIGIN.split(",").map((s) => s.trim());

  const token = await new SignJWT(payload)
    .setProtectedHeader({ alg: "ES256", kid: keyId })
    .setIssuer(teamId)
    .setIssuedAt(now)
    .setExpirationTime(now + ttl)
    .sign(key);

  cached = { token, expires: now + ttl };
  return token;
}

const storefront = () => (process.env.APPLE_STOREFRONT || "us").toLowerCase();

interface RawSong {
  id: string;
  attributes?: {
    name: string;
    artistName: string;
    albumName: string;
    releaseDate?: string;
    durationInMillis?: number;
    url?: string;
    artwork?: { url: string };
  };
}

async function appleFetch(path: string, init: RequestInit = {}, userToken?: string): Promise<Response> {
  const token = await getDeveloperToken();
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (userToken) headers.set("Music-User-Token", userToken);
  if (init.body) headers.set("Content-Type", "application/json");
  for (let attempt = 0; attempt < 3; attempt++) {
    const res = await fetch(`${API}${path}`, { ...init, headers, cache: "no-store" });
    if (res.status !== 429) return res;
    await new Promise((r) => setTimeout(r, 800 * (attempt + 1)));
  }
  throw new AppleMusicError("Apple Music rate limit hit, try again in a moment", 429);
}

async function searchCatalog(term: string): Promise<RawCandidate[]> {
  const qs = new URLSearchParams({ term, types: "songs", limit: "25" });
  const res = await appleFetch(`/catalog/${storefront()}/search?${qs}`);
  if (!res.ok) throw new AppleMusicError(`Apple Music search failed (${res.status})`, res.status);
  const json = (await res.json()) as { results?: { songs?: { data?: RawSong[] } } };
  return (json.results?.songs?.data ?? [])
    .filter((s) => s.attributes)
    .map((s) => {
      const a = s.attributes!;
      return {
        id: s.id,
        name: a.name,
        artistName: a.artistName,
        albumName: a.albumName,
        releaseDate: a.releaseDate,
        durationMs: a.durationInMillis,
        url: a.url,
        artworkUrl: a.artwork?.url.replace("{w}", "120").replace("{h}", "120"),
      };
    });
}

async function bestFor(song: SetlistSong, artist: string): Promise<TrackCandidate[]> {
  const target = { ...song, artist };
  // Strip setlist.fm annotations like "Walk This Way (with Run-DMC)" from the search term.
  const cleanTitle = song.title.replace(/[([].*?[)\]]/g, " ").replace(/\s+/g, " ").trim();
  let ranked = rankCandidates(target, await searchCatalog(`${cleanTitle} ${artist}`));

  // Some catalogs index oddly; retry with just the title if nothing usable came back.
  if (!ranked[0] || ranked[0].score < MIN_ACCEPTABLE) {
    const retry = rankCandidates(target, await searchCatalog(cleanTitle));
    if (retry[0] && (!ranked[0] || retry[0].score > ranked[0].score)) ranked = retry;
  }
  return ranked;
}

/**
 * Finds the best studio recording for one setlist song. Covers prefer the band's own
 * studio recording and fall back to the original artist's.
 */
export async function matchSong(song: SetlistSong): Promise<TrackMatch> {
  let ranked = await bestFor(song, song.artist);
  if (song.originalArtist && (!ranked[0] || ranked[0].score < HIGH_CONFIDENCE)) {
    const original = await bestFor(song, song.originalArtist);
    const seen = new Set(ranked.map((c) => c.id));
    ranked = [...ranked, ...original.filter((c) => !seen.has(c.id))].sort((a, b) => b.score - a.score);
  }

  const best = ranked[0] && ranked[0].score >= MIN_ACCEPTABLE ? ranked[0] : undefined;
  return {
    song,
    best,
    alternates: ranked.slice(0, 8),
    confidence: !best ? "none" : best.score >= HIGH_CONFIDENCE ? "high" : "low",
  };
}

/** Matches many songs with limited concurrency to stay friendly with Apple's rate limits. */
export async function matchSongs(songs: SetlistSong[], concurrency = 4): Promise<TrackMatch[]> {
  const out: TrackMatch[] = new Array(songs.length);
  let next = 0;
  async function worker() {
    while (next < songs.length) {
      const i = next++;
      try {
        out[i] = await matchSong(songs[i]);
      } catch (e) {
        if (e instanceof AppleMusicError && e.status >= 500 && e.message.includes("configured")) throw e;
        out[i] = { song: songs[i], alternates: [], confidence: "none" };
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, songs.length) }, worker));
  return out;
}

/** Creates a playlist in the signed-in user's Apple Music library. */
export async function createLibraryPlaylist(
  userToken: string,
  name: string,
  description: string,
  trackIds: string[],
): Promise<{ id: string }> {
  const body = {
    attributes: { name, description },
    relationships: { tracks: { data: trackIds.map((id) => ({ id, type: "songs" })) } },
  };
  const res = await appleFetch("/me/library/playlists", { method: "POST", body: JSON.stringify(body) }, userToken);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new AppleMusicError(`Couldn't create the playlist (${res.status}) ${text.slice(0, 200)}`, res.status);
  }
  const json = (await res.json()) as { data?: { id: string }[] };
  const id = json.data?.[0]?.id;
  if (!id) throw new AppleMusicError("Apple Music didn't return a playlist id", 502);
  return { id };
}
