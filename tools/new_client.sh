#!/usr/bin/env bash
# Scaffold a client folder: tools/new_client.sh "Jane Doe"
set -euo pipefail
name="${1:?Usage: new_client.sh \"Client Name\"}"
root="$(cd "$(dirname "$0")/.." && pwd)"
slug="$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-|-$//g')"
dir="$root/clients/$slug"

if [ -e "$dir" ]; then echo "Already exists: $dir" >&2; exit 1; fi
mkdir -p "$dir/evidence"
cp "$root/templates/intake.md" "$dir/intake.md"
sed "s/{{Client Name}}/$name/" "$root/templates/site-brief.md" > "$dir/site-brief.md"
cat > "$dir/audit.json" <<EOF
{
  "client": { "name": "$name", "type": "individual", "tagline": "", "date": "$(date +%Y-%m-%d)", "prepared_by": "SetPlay" },
  "summary": "",
  "pillars": [
    { "id": "discoverability", "name": "Discoverability",      "weight": 20, "score": null, "notes": "" },
    { "id": "consistency",     "name": "Consistency",          "weight": 15, "score": null, "notes": "" },
    { "id": "ownership",       "name": "Ownership & Control",  "weight": 20, "score": null, "notes": "" },
    { "id": "privacy",         "name": "Privacy & Safety",     "weight": 20, "score": null, "notes": "" },
    { "id": "reputation",      "name": "Reputation & Content", "weight": 10, "score": null, "notes": "" },
    { "id": "website",         "name": "Website Quality",      "weight": 15, "score": null, "notes": "" }
  ],
  "search_snapshot": [],
  "inventory": [],
  "findings": [],
  "roadmap": { "now": [], "next": [], "later": [] }
}
EOF
echo "Created $dir"
echo "Next: have the client complete intake.md, then run /footprint-audit $slug"
