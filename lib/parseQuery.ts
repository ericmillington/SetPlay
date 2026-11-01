import type { ParsedQuery } from "./types";

const MONTHS: Record<string, number> = {
  jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
  jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12,
};

const pad = (n: number) => String(n).padStart(2, "0");
const toSetlistDate = (d: number, m: number, y: number) => `${pad(d)}-${pad(m)}-${y}`;

const valid = (d: number, m: number) => d >= 1 && d <= 31 && m >= 1 && m <= 12;

interface DateHit {
  date?: string;
  year: string;
  index: number;
  length: number;
}

/** Finds a full date (or failing that, a year) in free text. */
function findDate(text: string): DateHit | undefined {
  const monthNames = "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?";
  const patterns: { re: RegExp; build: (m: RegExpMatchArray) => [number, number, number] | undefined }[] = [
    // 1990-08-23
    { re: /\b(\d{4})-(\d{1,2})-(\d{1,2})\b/, build: (m) => [+m[3], +m[2], +m[1]] },
    // 8/23/1990 (US order)
    { re: /\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b/, build: (m) => [+m[2], +m[1], +m[3]] },
    // August 23, 1990 / Aug 23rd 1990
    {
      re: new RegExp(`\\b(${monthNames})\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?,?\\s+(\\d{4})\\b`, "i"),
      build: (m) => [+m[2], MONTHS[m[1].slice(0, 3).toLowerCase()], +m[3]],
    },
    // 23 August 1990
    {
      re: new RegExp(`\\b(\\d{1,2})(?:st|nd|rd|th)?\\s+(?:of\\s+)?(${monthNames})\\.?,?\\s+(\\d{4})\\b`, "i"),
      build: (m) => [+m[1], MONTHS[m[2].slice(0, 3).toLowerCase()], +m[3]],
    },
  ];

  for (const { re, build } of patterns) {
    const m = text.match(re);
    if (m && m.index !== undefined) {
      const parts = build(m);
      if (parts && valid(parts[0], parts[1])) {
        return { date: toSetlistDate(...parts), year: String(parts[2]), index: m.index, length: m[0].length };
      }
    }
  }

  // "summer of '90" style two-digit years are ambiguous; only accept four digits.
  const y = text.match(/\b(19[5-9]\d|20\d{2})\b/);
  if (y && y.index !== undefined) return { year: y[1], index: y.index, length: y[0].length };
  return undefined;
}

/**
 * Turns something like "I saw Aerosmith at SPAC in 1990" into
 * { artist: "Aerosmith", venue: "SPAC", year: "1990" }.
 */
export function parseQuery(input: string): ParsedQuery {
  let text = input.trim().replace(/\s+/g, " ");

  // Drop conversational lead-ins.
  text = text.replace(/^(?:i|we)\s+(?:saw|went to see|caught|heard)\s+/i, "");
  text = text.replace(/^(?:saw|seeing|caught)\s+/i, "");
  text = text.replace(/[.!?]+$/, "");

  const result: ParsedQuery = { artist: "" };

  const hit = findDate(text);
  if (hit) {
    result.year = hit.year;
    if (hit.date) result.date = hit.date;
    const before = text.slice(0, hit.index).replace(/\b(?:back\s+in|in|on|during|around|circa)\s*$/i, "");
    const after = text.slice(hit.index + hit.length);
    text = `${before} ${after}`;
  }

  text = text.replace(/\s+/g, " ").replace(/[\s,;-]+$/, "").replace(/^[\s,;-]+/, "").trim();

  // Split artist from venue on " at ", " @ ", or the first comma.
  const split = text.match(/^(.+?)\s+(?:at|@)\s+(?:the\s+)?(.+)$/i) ?? text.match(/^(.+?),\s*(.+)$/);
  if (split) {
    result.artist = split[1].trim();
    result.venue = split[2].replace(/^(?:the)\s+/i, "").replace(/,\s*$/, "").trim();
  } else {
    result.artist = text;
  }

  return result;
}
