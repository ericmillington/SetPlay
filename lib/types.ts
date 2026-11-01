/** Shapes shared between the server routes and the browser. */

export interface ParsedQuery {
  artist: string;
  venue?: string;
  /** Four-digit year, e.g. "1990". */
  year?: string;
  /** setlist.fm date format: dd-MM-yyyy. */
  date?: string;
}

export interface SetlistSong {
  /** Song title as written on setlist.fm. */
  title: string;
  /** The band that played it. */
  artist: string;
  /** For covers: the original artist, used if the band never recorded it themselves. */
  originalArtist?: string;
  isCover: boolean;
  /** Name of the set this song was played in, e.g. "Encore". */
  setName?: string;
  info?: string;
}

export interface Show {
  id: string;
  /** dd-MM-yyyy, as setlist.fm returns it. */
  eventDate: string;
  artist: string;
  venue: string;
  city: string;
  state?: string;
  country?: string;
  tour?: string;
  url: string;
  songs: SetlistSong[];
}

export interface TrackCandidate {
  id: string;
  name: string;
  artistName: string;
  albumName: string;
  releaseDate?: string;
  durationMs?: number;
  url?: string;
  artworkUrl?: string;
  score: number;
}

export interface TrackMatch {
  song: SetlistSong;
  best?: TrackCandidate;
  alternates: TrackCandidate[];
  confidence: "high" | "low" | "none";
}
