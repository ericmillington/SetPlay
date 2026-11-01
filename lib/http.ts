import { NextResponse } from "next/server";
import { AppleMusicError } from "./appleMusic";
import { SetlistFmError } from "./setlistfm";

export function errorResponse(e: unknown) {
  if (e instanceof AppleMusicError || e instanceof SetlistFmError) {
    const status = e.status >= 400 && e.status < 600 ? e.status : 502;
    return NextResponse.json({ error: e.message }, { status });
  }
  console.error(e);
  return NextResponse.json({ error: "Something went wrong" }, { status: 500 });
}
