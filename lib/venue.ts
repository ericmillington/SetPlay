/** Fuzzy venue matching so "SPAC" or "Saratoga" finds "Saratoga Performing Arts Center". */

const ALIASES: Record<string, string> = {
  msg: "Madison Square Garden",
  "the garden": "Madison Square Garden",
  "red rocks": "Red Rocks Amphitheatre",
  "the spectrum": "Spectrum",
  "the forum": "Forum",
  "jones beach": "Jones Beach Theater",
  "pine knob": "Pine Knob Music Theatre",
  "alpine valley": "Alpine Valley Music Theatre",
  "shoreline": "Shoreline Amphitheatre",
  "the gorge": "Gorge Amphitheatre",
  "merriweather": "Merriweather Post Pavilion",
  "great woods": "Great Woods Center for the Performing Arts",
  "the meadows": "Meadows Music Theatre",
  "the fillmore": "Fillmore",
};

const STOP = new Set(["the", "of", "and", "at", "in", "a", "&"]);

export function normalizeWords(s: string): string[] {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((w) => w && !STOP.has(w));
}

function initials(s: string): string {
  return normalizeWords(s).map((w) => w[0]).join("");
}

export function expandVenueAlias(query: string): string {
  return ALIASES[query.trim().toLowerCase()] ?? query;
}

/**
 * Scores 0..1 how well a venue query matches a setlist.fm venue + city.
 * 1 means every word in the query (or its acronym) was found.
 */
export function venueScore(query: string, venueName: string, cityName = "", state = ""): number {
  const q = query.trim();
  if (!q) return 0;

  const expanded = expandVenueAlias(q);
  const qWords = normalizeWords(expanded);
  if (qWords.length === 0) return 0;

  // Acronym, e.g. SPAC -> Saratoga Performing Arts Center
  const compact = q.replace(/[^a-z0-9]/gi, "").toLowerCase();
  if (compact.length >= 2 && /^[a-z]+$/.test(compact) && initials(venueName) === compact) return 1;

  const haystack = new Set([...normalizeWords(venueName), ...normalizeWords(cityName), ...normalizeWords(state)]);
  const found = qWords.filter((w) => haystack.has(w) || [...haystack].some((h) => h.length > 3 && (h.startsWith(w) || w.startsWith(h)))).length;
  return found / qWords.length;
}
