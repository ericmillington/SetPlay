import { NextResponse, type NextRequest } from "next/server";
import { createLibraryPlaylist } from "@/lib/appleMusic";
import { errorResponse } from "@/lib/http";

/** POST /api/playlist { musicUserToken, name, description, trackIds } */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as {
    musicUserToken?: string;
    name?: string;
    description?: string;
    trackIds?: string[];
  } | null;

  const userToken = body?.musicUserToken;
  const trackIds = (body?.trackIds ?? []).filter((id) => typeof id === "string" && /^\d+$/.test(id));
  if (!userToken) return NextResponse.json({ error: "Sign in to Apple Music first" }, { status: 401 });
  if (trackIds.length === 0) return NextResponse.json({ error: "No tracks selected" }, { status: 400 });

  const name = (body?.name || "SetPlay").slice(0, 100);
  const description = (body?.description || "").slice(0, 300);

  try {
    const { id } = await createLibraryPlaylist(userToken, name, description, trackIds);
    return NextResponse.json({ id, url: `https://music.apple.com/library/playlist/${id}` });
  } catch (e) {
    return errorResponse(e);
  }
}
