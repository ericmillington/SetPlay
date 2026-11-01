import type { SetlistSong, TrackCandidate } from "./types";

/** Normalizes a song title for comparison: drops "(Remastered 2001)", "- Single Version", feat. credits, punctuation. */
export function normalizeTitle(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/\s+-\s+.*$/, "") // "Dream On - 2011 Remaster"
    .replace(/[([].*?[)\]]/g, " ") // "(feat. X)", "[Live]"
    .replace(/&/g, " and ")
    .replace(/[’']/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function normalizeArtist(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/^the\s+/, "")
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Words that mark a recording as something other than the original studio take. */
const NON_STUDIO = [
  /\blive\b/, /\bdemo\b/, /\bacoustic\b/, /\bunplugged\b/, /\bremix(?:ed)?\b/, /\bkaraoke\b/,
  /\binstrumental\b/, /\btribute\b/, /\boriginally performed\b/, /\bin the style of\b/,
  /\brehearsal\b/, /\bbbc\b/, /\bouttake\b/, /\balternate\b/, /\breimagined\b/,
  /\borchestral\b/, /\blullaby\b/, /\bre-?recorded\b/,
];
/** Weaker signals: often still the studio take ("Single Version", "Radio Edit"), so only nudge. */
const MAYBE_NON_STUDIO = [/\bedit\b/, /\bmix\b/, /\bversion\b/, /\bsession\b/, /\bmono\b/];
const COMPILATION = [
  /greatest hits/, /\bbest of\b/, /\bessential\b/, /\bcollection\b/, /\banthology\b/, /\bhits\b/,
  /\bgold\b/, /\bvery best\b/, /\bultimate\b/, /\bdefinitive\b/, /\bplatinum\b/, /\bcompilation\b/,
  /\bnow that'?s what\b/, /\b\d+s\b/, /\bsoundtrack\b/,
];

const words = (s: string) => new Set(s.split(" ").filter(Boolean));

function overlap(a: string, b: string): number {
  const A = words(a);
  const B = words(b);
  if (A.size === 0 || B.size === 0) return 0;
  let n = 0;
  for (const w of A) if (B.has(w)) n++;
  return n / Math.max(A.size, B.size);
}

export interface RawCandidate {
  id: string;
  name: string;
  artistName: string;
  albumName: string;
  releaseDate?: string;
  durationMs?: number;
  url?: string;
  artworkUrl?: string;
}

/** Scores a single candidate, ignoring release date (applied across candidates in rankCandidates). */
export function scoreCandidate(song: SetlistSong, c: RawCandidate): number {
  const wantTitle = normalizeTitle(song.title);
  const gotTitle = normalizeTitle(c.name);
  const wantArtist = normalizeArtist(song.artist);
  const gotArtist = normalizeArtist(c.artistName);

  let score = 0;

  if (wantTitle === gotTitle) score += 50;
  else if (gotTitle.startsWith(wantTitle) || wantTitle.startsWith(gotTitle)) score += 30;
  else score += overlap(wantTitle, gotTitle) * 25;

  if (wantArtist === gotArtist) score += 35;
  else if (gotArtist.includes(wantArtist) || wantArtist.includes(gotArtist)) score += 22;
  else if (overlap(wantArtist, gotArtist) > 0) score += 8;
  else score -= 40;

  // Penalize live/demo/remix etc., unless the setlist itself names that version.
  const wantRaw = song.title.toLowerCase();
  const nameRaw = c.name.toLowerCase();
  const albumRaw = c.albumName.toLowerCase();
  for (const re of NON_STUDIO) {
    if (re.test(wantRaw)) continue;
    if (re.test(nameRaw)) score -= 30;
    else if (re.test(albumRaw)) score -= 20;
  }
  for (const re of MAYBE_NON_STUDIO) {
    if (!re.test(wantRaw) && re.test(nameRaw)) score -= 6;
  }
  for (const re of COMPILATION) {
    if (re.test(albumRaw)) {
      score -= 8;
      break;
    }
  }
  if (/remaster/.test(nameRaw) || /remaster/.test(albumRaw)) score -= 2;

  return score;
}

/** Ranks candidates best-first. Among equals, the earliest release (the original album) wins. */
export function rankCandidates(song: SetlistSong, raws: RawCandidate[]): TrackCandidate[] {
  const years = raws.map((r) => Number(r.releaseDate?.slice(0, 4))).filter((y) => y > 0);
  const minYear = years.length ? Math.min(...years) : 0;
  return raws
    .map((r) => {
      let score = scoreCandidate(song, r);
      const y = Number(r.releaseDate?.slice(0, 4));
      if (minYear && y > 0) score -= Math.min(10, (y - minYear) * 0.3);
      return { ...r, score: Math.round(score * 10) / 10 };
    })
    .sort((a, b) => b.score - a.score);
}

export const HIGH_CONFIDENCE = 70;
export const MIN_ACCEPTABLE = 45;
