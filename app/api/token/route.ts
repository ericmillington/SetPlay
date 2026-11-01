import { NextResponse } from "next/server";
import { getDeveloperToken } from "@/lib/appleMusic";
import { errorResponse } from "@/lib/http";

/** Developer token for MusicKit JS in the browser (needed to sign the user in to Apple Music). */
export async function GET() {
  try {
    return NextResponse.json({ token: await getDeveloperToken() }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    return errorResponse(e);
  }
}
