"use client";

/** Minimal typings for the bits of MusicKit JS v3 we use. */
interface MusicKitInstance {
  authorize(): Promise<string>;
  unauthorize(): Promise<void>;
  isAuthorized: boolean;
  musicUserToken: string;
}
declare global {
  interface Window {
    MusicKit?: {
      configure(opts: { developerToken: string; app: { name: string; build: string } }): Promise<MusicKitInstance>;
      getInstance(): MusicKitInstance;
    };
  }
}

const SCRIPT = "https://js-cdn.music.apple.com/musickit/v3/musickit.js";
let ready: Promise<MusicKitInstance> | undefined;

function loadScript(): Promise<void> {
  if (window.MusicKit) return Promise.resolve();
  return new Promise((resolve, reject) => {
    document.addEventListener("musickitloaded", () => resolve(), { once: true });
    const s = document.createElement("script");
    s.src = SCRIPT;
    s.async = true;
    s.dataset.webComponents = "";
    s.onerror = () => reject(new Error("Couldn't load MusicKit from Apple"));
    document.head.appendChild(s);
  });
}

/** Loads and configures MusicKit once per page. */
export function getMusicKit(): Promise<MusicKitInstance> {
  ready ??= (async () => {
    const res = await fetch("/api/token");
    const json = await res.json();
    if (!res.ok) throw new Error(json.error ?? "Couldn't get an Apple Music token");
    await loadScript();
    return window.MusicKit!.configure({ developerToken: json.token, app: { name: "SetPlay", build: "0.1.0" } });
  })().catch((e) => {
    ready = undefined;
    throw e;
  });
  return ready;
}

/** Signs the user in to Apple Music (opens Apple's popup) and returns their Music User Token. */
export async function signInToAppleMusic(): Promise<string> {
  const mk = await getMusicKit();
  if (mk.isAuthorized && mk.musicUserToken) return mk.musicUserToken;
  return mk.authorize();
}
