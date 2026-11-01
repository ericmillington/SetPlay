"use client";

import { useMemo, useState } from "react";
import type { ParsedQuery, Show, TrackCandidate, TrackMatch } from "@/lib/types";
import { signInToAppleMusic } from "@/lib/musickit";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function prettyDate(d: string) {
  const [dd, mm, yyyy] = d.split("-");
  return `${MONTHS[Number(mm) - 1]} ${Number(dd)}, ${yyyy}`;
}
const place = (s: Show) => [s.city, s.state, s.country].filter(Boolean).join(", ");
const year = (c?: TrackCandidate) => c?.releaseDate?.slice(0, 4);

interface Row {
  match: TrackMatch;
  chosenId?: string;
  include: boolean;
}

export default function Home() {
  const [q, setQ] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [adv, setAdv] = useState({ artist: "", venue: "", year: "", date: "" });

  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string>();
  const [parsed, setParsed] = useState<ParsedQuery>();
  const [shows, setShows] = useState<Show[]>();

  const [show, setShow] = useState<Show>();
  const [matching, setMatching] = useState(false);
  const [rows, setRows] = useState<Row[]>([]);

  const [playlistName, setPlaylistName] = useState("");
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<{ url: string; count: number }>();

  async function search(e: React.FormEvent) {
    e.preventDefault();
    setError(undefined);
    setShows(undefined);
    setShow(undefined);
    setCreated(undefined);
    setSearching(true);
    try {
      const params = new URLSearchParams({ q });
      if (adv.artist) params.set("artist", adv.artist);
      if (adv.venue) params.set("venue", adv.venue);
      if (adv.year) params.set("year", adv.year);
      if (adv.date) {
        const [y, m, d] = adv.date.split("-");
        params.set("date", `${d}-${m}-${y}`);
      }
      const res = await fetch(`/api/setlists?${params}`);
      const json = await res.json();
      if (!res.ok) throw new Error(json.error);
      setParsed(json.query);
      setShows(json.shows);
    } catch (err) {
      setError((err as Error).message || "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function pick(s: Show) {
    setShow(s);
    setRows([]);
    setCreated(undefined);
    setError(undefined);
    setPlaylistName(`${s.artist} — ${s.venue}, ${prettyDate(s.eventDate)}`);
    if (s.songs.length === 0) return;
    setMatching(true);
    try {
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ songs: s.songs }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error);
      setRows(
        (json.matches as TrackMatch[]).map((m) => ({ match: m, chosenId: m.best?.id, include: Boolean(m.best) })),
      );
    } catch (err) {
      setError((err as Error).message || "Matching failed");
    } finally {
      setMatching(false);
    }
  }

  const selectedIds = useMemo(
    () => rows.filter((r) => r.include && r.chosenId).map((r) => r.chosenId!),
    [rows],
  );

  async function createPlaylist() {
    if (!show) return;
    setError(undefined);
    setCreating(true);
    try {
      const musicUserToken = await signInToAppleMusic();
      const res = await fetch("/api/playlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          musicUserToken,
          name: playlistName,
          description: `Studio versions of the setlist from ${show.artist} at ${show.venue}, ${place(show)} on ${prettyDate(show.eventDate)}. Setlist via setlist.fm. Made with SetPlay.`,
          trackIds: selectedIds,
        }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error);
      setCreated({ url: json.url, count: selectedIds.length });
    } catch (err) {
      setError((err as Error).message || "Couldn't create the playlist");
    } finally {
      setCreating(false);
    }
  }

  const update = (i: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, ...patch } : r)));

  return (
    <main>
      <header className="hero">
        <h1>
          Set<span>Play</span>
        </h1>
        <p>Tell us a show you saw. We'll find the setlist and build an Apple Music playlist of the studio versions, in the order they played them.</p>
      </header>

      <form className="search" onSubmit={search}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="I saw Aerosmith at SPAC in 1990"
          aria-label="Describe the show"
          autoFocus
        />
        <button type="submit" disabled={searching || (!q.trim() && !adv.artist.trim())}>
          {searching ? "Searching…" : "Find the show"}
        </button>
      </form>
      <button className="linklike" onClick={() => setShowAdvanced((v) => !v)}>
        {showAdvanced ? "Hide" : "More"} search options
      </button>
      {showAdvanced && (
        <div className="advanced">
          <label>Artist<input value={adv.artist} onChange={(e) => setAdv({ ...adv, artist: e.target.value })} /></label>
          <label>Venue or city<input value={adv.venue} onChange={(e) => setAdv({ ...adv, venue: e.target.value })} /></label>
          <label>Year<input inputMode="numeric" maxLength={4} value={adv.year} onChange={(e) => setAdv({ ...adv, year: e.target.value })} /></label>
          <label>Exact date<input type="date" value={adv.date} onChange={(e) => setAdv({ ...adv, date: e.target.value })} /></label>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      {shows && !show && (
        <section>
          {parsed && (
            <p className="muted">
              Looking for <b>{parsed.artist}</b>
              {parsed.venue && <> at <b>{parsed.venue}</b></>}
              {parsed.date ? <> on <b>{prettyDate(parsed.date)}</b></> : parsed.year && <> in <b>{parsed.year}</b></>}
            </p>
          )}
          {shows.length === 0 ? (
            <p>No shows found on setlist.fm. Try just the artist and year, or check the spelling.</p>
          ) : (
            <ul className="shows">
              {shows.map((s) => (
                <li key={s.id}>
                  <button onClick={() => pick(s)}>
                    <span className="date">{prettyDate(s.eventDate)}</span>
                    <span className="venue">{s.venue}</span>
                    <span className="muted">{place(s)}{s.tour ? ` · ${s.tour}` : ""}</span>
                    <span className="count">{s.songs.length ? `${s.songs.length} songs` : "no setlist yet"}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {show && (
        <section>
          <button className="linklike" onClick={() => setShow(undefined)}>← Back to shows</button>
          <h2>{show.artist}</h2>
          <p className="muted">
            {show.venue}, {place(show)} · {prettyDate(show.eventDate)}
            {show.tour && <> · {show.tour}</>} · <a href={show.url} target="_blank" rel="noreferrer">setlist.fm</a>
          </p>

          {show.songs.length === 0 && <p>setlist.fm doesn't have the songs for this show yet.</p>}
          {matching && <p className="muted">Finding studio recordings on Apple Music…</p>}

          {rows.length > 0 && (
            <>
              <ol className="tracks">
                {rows.map((r, i) => {
                  const prevSet = i > 0 ? rows[i - 1].match.song.setName : undefined;
                  const setName = r.match.song.setName;
                  const chosen = r.match.alternates.find((a) => a.id === r.chosenId);
                  return (
                    <li key={i} className={r.include ? "" : "off"}>
                      {setName && setName !== prevSet && <div className="setname">{setName}</div>}
                      <div className="track">
                        <input
                          type="checkbox"
                          checked={r.include}
                          disabled={!r.chosenId}
                          onChange={(e) => update(i, { include: e.target.checked })}
                          aria-label={`Include ${r.match.song.title}`}
                        />
                        {chosen?.artworkUrl ? <img src={chosen.artworkUrl} alt="" /> : <div className="noart" />}
                        <div className="meta">
                          <div className="title">
                            {r.match.song.title}
                            {r.match.song.isCover && <span className="tag">cover · {r.match.song.originalArtist}</span>}
                            {r.match.confidence === "low" && r.chosenId === r.match.best?.id && <span className="tag warn">check this</span>}
                          </div>
                          {r.match.alternates.length > 0 ? (
                            <select value={r.chosenId ?? ""} onChange={(e) => update(i, { chosenId: e.target.value || undefined, include: Boolean(e.target.value) })}>
                              {!r.match.best && <option value="">No good match — pick one</option>}
                              {r.match.alternates.map((a) => (
                                <option key={a.id} value={a.id}>
                                  {a.name} — {a.artistName} · {a.albumName}{year(a) ? ` (${year(a)})` : ""}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <span className="muted">Not found on Apple Music</span>
                          )}
                        </div>
                        {chosen?.url && <a className="open" href={chosen.url} target="_blank" rel="noreferrer">Open</a>}
                      </div>
                    </li>
                  );
                })}
              </ol>

              <div className="create">
                <input value={playlistName} onChange={(e) => setPlaylistName(e.target.value)} aria-label="Playlist name" />
                <button onClick={createPlaylist} disabled={creating || selectedIds.length === 0}>
                  {creating ? "Creating…" : `Add ${selectedIds.length} songs to Apple Music`}
                </button>
              </div>
              {created && (
                <p className="success">
                  Done — {created.count} songs added. <a href={created.url} target="_blank" rel="noreferrer">Open the playlist in Apple Music</a>
                </p>
              )}
            </>
          )}
        </section>
      )}

      <footer>Setlists from <a href="https://www.setlist.fm" target="_blank" rel="noreferrer">setlist.fm</a>. Music from Apple Music.</footer>
    </main>
  );
}
