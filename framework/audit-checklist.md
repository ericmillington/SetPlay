# Footprint Audit Checklist

Work through every pillar. Record each item in `audit.json`: account-type items go in
`inventory`, problems go in `findings`, and fixes go in `roadmap`. Capture evidence (a URL
or a screenshot filename) for every finding. Note the date, because search results change.

**Ground rules:** written consent first. Use public information only. Don't log in as
the client unless they hand you access for the cleanup phase. Don't create accounts on
data broker sites to see full records.

---

## 1. Discoverability: "What happens when someone looks you up?"

Search in a private/incognito window, signed out. Record the top 10 results for each query.

- [ ] `"Full Name"`
- [ ] `"Full Name" + city`
- [ ] `"Full Name" + profession / business name`
- [ ] Business name alone (for businesses)
- [ ] Common misspellings / maiden or former names (with consent)
- [ ] Image search for the name: are the photos actually of them?
- [ ] For each result, note whether the client owns it, whether it's about them or a namesake, and its sentiment
- [ ] Is there a knowledge panel? Is it accurate?
- [ ] Google Business Profile / Apple Maps / Bing Places (for local businesses)

## 2. Consistency: "Do you look like the same person everywhere?"

For every profile found:

- [ ] Display name matches
- [ ] Headshot / logo is current and the same everywhere
- [ ] Bio/headline tells the same story (role, specialty, location)
- [ ] Links point to the right place (the website and current contact info)
- [ ] Handles are consistent (ideally the same handle on every platform)
- [ ] NAP (Name, Address, Phone) is consistent for local businesses

## 3. Ownership & Control: "Do you actually control your presence?"

- [ ] Own domain? Who is the registrant? When does it expire? Is auto-renew on?
- [ ] Is the website on an account in the client's name?
- [ ] Professional email on their own domain (not only gmail/hotmail)?
- [ ] Is the preferred handle available or taken on the major platforms? (Note whether it's free to reserve.)
- [ ] Dormant accounts the client has forgotten (ask them about MySpace-era and old employers' pages)
- [ ] Impersonation or lookalike accounts
- [ ] Ask the client whether 2FA is enabled on email, domain registrar, and main socials
- [ ] Ask the client whether account recovery uses old emails or phone numbers they no longer have

## 4. Privacy & Safety: "What's exposed that shouldn't be?"

- [ ] Data broker / people-search listings (Spokeo, Whitepages, BeenVerified, FastPeopleSearch, TruePeopleSearch, Radaris, MyLife, Intelius…). Record whether the name appears; don't buy reports.
- [ ] Home address publicly visible (WHOIS, business filings, old listings, the site footer)
- [ ] Personal phone or email exposed
- [ ] Breach exposure: check the client's email(s) at haveibeenpwned.com with their consent, and record breach *names* only
- [ ] Photos revealing location, kids, house, or routine
- [ ] Family members named and linked
- [ ] Public Venmo / Strava / Spotify / Amazon wishlist and similar "leaky" apps

## 5. Reputation & Content: "What story does the internet tell?"

- [ ] Reviews (Google, Yelp, industry-specific): count, average, and recency. Are owner responses present?
- [ ] Press mentions, podcasts, talks, and awards that should be featured
- [ ] Outdated content (old jobs, old prices, closed locations)
- [ ] Content that may be off-brand or risky (old posts, tone). Flag it gently and let the client decide.
- [ ] Negative results: are they legitimate? Is there a fair response?
- [ ] Namesakes who might be confused with the client (especially ones with negative coverage)

## 6. Website Quality: "Is your home base doing its job?"

Run `python3 tools/site_check.py <url>` and save it as `site-check.json`. Then check by hand:

- [ ] HTTPS, with http → https redirect
- [ ] Mobile-friendly (viewport, readable without zoom)
- [ ] Title and meta description that use their name and what they do
- [ ] Open Graph tags, so links look good when shared
- [ ] Accessibility: `lang` attribute, image alt text, heading structure, contrast
- [ ] Page weight and speed (run PageSpeed Insights by hand for Core Web Vitals)
- [ ] Third-party trackers present? Is a cookie banner needed?
- [ ] Security headers (HSTS, CSP, X-Content-Type-Options, Referrer-Policy)
- [ ] Clear call to action: what should a visitor do next?
- [ ] Broken links, dead forms, placeholder content, and a stale copyright year
- [ ] If there's no website, score this pillar 0 and make the website the #1 roadmap item
