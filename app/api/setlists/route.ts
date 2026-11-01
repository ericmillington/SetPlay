import { NextResponse, type NextRequest } from "next/server";
import { parseQuery } from "@/lib/parseQuery";
import { findShows } from "@/lib/setlistfm";
import { errorResponse } from "@/lib/http";
import type { ParsedQuery } from "@/lib/types";

/**
 * GET /api/setlists?q=Aerosmith at SPAC in 1990
 * Optional overrides: artist, venue, year, date (dd-MM-yyyy).
 */
export async function GET(req: NextRequest) {
  const apiKey = process.env.SETLISTFM_API_KEY;
  if (!apiKey) return NextResponse.json({ error: "SETLISTFM_API_KEY isn't set" }, { status: 500 });

  const sp = req.nextUrl.searchParams;
  const parsed: ParsedQuery = parseQuery(sp.get("q") ?? "");
  for (const k of ["artist", "venue", "year", "date"] as const) {
    const v = sp.get(k)?.trim();
    if (v) parsed[k] = v;
  }
  if (parsed.date && !/^\d{2}-\d{2}-\d{4}$/.test(parsed.date)) {
    return NextResponse.json({ error: "date must be dd-MM-yyyy" }, { status: 400 });
  }
  if (!parsed.artist) return NextResponse.json({ error: "Tell me which band you saw" }, { status: 400 });

  try {
    const shows = await findShows(parsed, apiKey);
    return NextResponse.json({ query: parsed, shows: shows.slice(0, 30) });
  } catch (e) {
    return errorResponse(e);
  }
}
