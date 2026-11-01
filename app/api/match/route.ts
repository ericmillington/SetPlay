import { NextResponse, type NextRequest } from "next/server";
import { matchSongs } from "@/lib/appleMusic";
import { errorResponse } from "@/lib/http";
import type { SetlistSong } from "@/lib/types";

/** POST /api/match { songs: SetlistSong[] } -> { matches: TrackMatch[] } */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as { songs?: SetlistSong[] } | null;
  const songs = (body?.songs ?? []).filter((s) => s && typeof s.title === "string" && typeof s.artist === "string");
  if (songs.length === 0) return NextResponse.json({ error: "No songs to match" }, { status: 400 });
  if (songs.length > 80) return NextResponse.json({ error: "That's a long show — 80 songs max" }, { status: 400 });

  try {
    return NextResponse.json({ matches: await matchSongs(songs) });
  } catch (e) {
    return errorResponse(e);
  }
}
