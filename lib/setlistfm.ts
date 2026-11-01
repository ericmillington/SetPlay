import type { ParsedQuery, SetlistSong, Show } from "./types";
import { expandVenueAlias, normalizeWords, venueScore } from "./venue";

const BASE = "https://api.setlist.fm/rest/1.0";

/* Raw setlist.fm response shapes (only the fields we use). */
interface RawSong {
  name?: string;
  tape?: boolean;
  info?: string;
  cover?: { name?: string };
  with?: { name?: string };
}
interface RawSet {
  name?: string;
  encore?: number;
  song?: RawSong[];
}
export interface RawSetlist {
  id: string;
  eventDate: string;
  url: string;
  artist: { name: string };
  venue: { name: string; city?: { name?: string; state?: string; stateCode?: string; country?: { name?: string } } };
  tour?: { name?: string };
  sets?: { set?: RawSet[] };
}
interface RawSearch {
  setlist?: RawSetlist[];
  total?: number;
  page?: number;
  itemsPerPage?: number;
}

export class SetlistFmError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

/** Flattens a setlist.fm setlist into the songs we want to look up, in order. */
export function toShow(raw: RawSetlist): Show {
  const songs: SetlistSong[] = [];
  for (const set of raw.sets?.set ?? []) {
    const setName = set.name ?? (set.encore ? (set.encore > 1 ? `Encore ${set.encore}` : "Encore") : undefined);
    for (const s of set.song ?? []) {
      const title = s.name?.trim();
      // Tapes are intro/outro recordings, not part of the performance.
      if (!title || s.tape) continue;
      const coverArtist = s.cover?.name?.trim();
      songs.push({
        title,
        artist: raw.artist.name,
        originalArtist: coverArtist || undefined,
        isCover: Boolean(coverArtist),
        setName,
        info: s.info,
      });
    }
  }
  const city = raw.venue.city;
  return {
    id: raw.id,
    eventDate: raw.eventDate,
    artist: raw.artist.name,
    venue: raw.venue.name,
    city: city?.name ?? "",
    state: city?.state ?? city?.stateCode,
    country: city?.country?.name,
    tour: raw.tour?.name,
    url: raw.url,
    songs,
  };
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function search(params: Record<string, string>, apiKey: string): Promise<RawSearch> {
  const url = `${BASE}/search/setlists?${new URLSearchParams(params)}`;
  for (let attempt = 0; attempt < 3; attempt++) {
    const res = await fetch(url, {
      headers: { "x-api-key": apiKey, Accept: "application/json" },
      cache: "no-store",
    });
    // setlist.fm returns 404 when a search has no results.
    if (res.status === 404) return { setlist: [], total: 0 };
    // Rate limited (2 requests/second on the free tier): back off and retry.
    if (res.status === 429) {
      await sleep(600 * (attempt + 1));
      continue;
    }
    if (!res.ok) throw new SetlistFmError(`setlist.fm returned ${res.status}`, res.status);
    return (await res.json()) as RawSearch;
  }
  throw new SetlistFmError("setlist.fm rate limit hit, try again in a moment", 429);
}

/** Fetches up to `maxPages` pages of results for the given search. */
async function searchPages(params: Record<string, string>, apiKey: string, maxPages: number): Promise<RawSetlist[]> {
  const out: RawSetlist[] = [];
  for (let p = 1; p <= maxPages; p++) {
    const page = await search({ ...params, p: String(p) }, apiKey);
    const items = page.setlist ?? [];
    out.push(...items);
    const total = page.total ?? 0;
    const per = page.itemsPerPage ?? 20;
    if (items.length === 0 || p * per >= total) break;
    await sleep(550);
  }
  return out;
}

const dateKey = (d: string) => d.split("-").reverse().join(""); // dd-MM-yyyy -> yyyyMMdd

/**
 * Finds shows matching a parsed query. Strategy:
 *  - with an exact date: ask setlist.fm for artist + date
 *  - with a year: pull the artist's shows that year and rank by how well the venue matches
 *  - with only a venue: ask setlist.fm for artist + venue name
 */
export async function findShows(q: ParsedQuery, apiKey: string): Promise<Show[]> {
  if (!q.artist.trim()) return [];
  const artistName = q.artist.trim();
  let raws: RawSetlist[];

  if (q.date) {
    raws = await searchPages({ artistName, date: q.date }, apiKey, 1);
  } else if (q.year) {
    raws = await searchPages({ artistName, year: q.year }, apiKey, 5);
  } else if (q.venue) {
    raws = await searchPages({ artistName, venueName: expandVenueAlias(q.venue) }, apiKey, 2);
    if (raws.length === 0) raws = await searchPages({ artistName, cityName: q.venue }, apiKey, 2);
  } else {
    raws = await searchPages({ artistName }, apiKey, 1);
  }

  // setlist.fm's artist search is loose ("Aerosmith" also returns tribute bands). Prefer exact names.
  const wanted = normalizeWords(artistName).join(" ");
  const exact = raws.filter((r) => normalizeWords(r.artist.name).join(" ") === wanted);
  if (exact.length > 0) raws = exact;

  let shows = raws.map(toShow);

  if (q.venue) {
    const scored = shows.map((s) => ({ s, v: venueScore(q.venue!, s.venue, s.city, s.state) }));
    const good = scored.filter((x) => x.v >= 0.5);
    // If nothing matches the venue, fall back to showing everything so the user can still pick.
    shows = (good.length > 0 ? good : scored)
      .sort((a, b) => b.v - a.v || dateKey(a.s.eventDate).localeCompare(dateKey(b.s.eventDate)))
      .map((x) => x.s);
  } else {
    shows.sort((a, b) => dateKey(a.eventDate).localeCompare(dateKey(b.eventDate)));
  }

  // Shows with a known setlist first.
  return [...shows.filter((s) => s.songs.length > 0), ...shows.filter((s) => s.songs.length === 0)];
}
