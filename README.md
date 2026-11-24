# Scraper test site

A minimal static site to validate the full scraper → portal flow:

**scrape → register as Pending Review → reviewer rejects → update content → re-scrape → reopen (or stay Rejected if Strictly Rejected).**

Not affiliated with any real organization. The Anthem policies page was only the
shape to imitate: one HTML page linking to one downloadable PDF.

## Files

| File | Purpose |
|---|---|
| `index.html` | Landing page linking to `policy.pdf` (one file for the scraper to find) |
| `policy.pdf` | The live file under test. **Starts as v1.** |
| `policy-v1.pdf` | Original content (same bytes as the starting `policy.pdf`) |
| `policy-v2.pdf` | **Updated** content — different text → different SHA-256 → detected as changed |

Keep the live file's name/URL as `policy.pdf` throughout. The portal keys a
re-scrape to the existing row by **BlobUrl**, so the URL must stay stable for the
re-scrape to be treated as an *update* and not a brand-new file.

## Why two real PDFs (not HTML→PDF)

The portal hashes a **downloaded** PDF raw. Changing the text changes the bytes,
so the content hash changes and the change is detected. (HTML→PDF "generated"
PDFs get their `/CreationDate` and `/ModDate` skipped during hashing — avoid that
subtlety for this test by serving real PDF files.)

## Hosting

### Option A — GitHub Pages (recommended: one public URL for both staging and local)

```bash
cd "C:/WindSurf Upgrade/scraper-test"
git init
git add .
git commit -m "Scraper test site"
git branch -M main
# create an empty repo on github.com first, then:
git remote add origin https://github.com/<you>/scraper-test.git
git push -u origin main
```

Then in the repo: **Settings → Pages → Build from branch `main` / root**.
Your file will be at:

```
https://<you>.github.io/scraper-test/policy.pdf
```

Reachable from both staging and your local scraper. Netlify / Cloudflare Pages
work the same way (drag-and-drop the folder) and give a stable HTTPS URL.

### Option B — Local only (local scraper run)

```bash
cd "C:/WindSurf Upgrade/scraper-test"
python -m http.server 8080
# http://localhost:8080/policy.pdf
```

`localhost` is **not** reachable from staging. To hit it from staging, expose it
with a tunnel (`ngrok http 8080` or a Cloudflare Tunnel) — note the free ngrok URL
changes on restart, so re-point the scraper's site config if you restart it.

## Register the site with the scraper

The crawler that POSTs to `api/scrappedfiles/register` is the separate **.NET 8
WebScraper** repo (not this one). Add this test site there as a **monitored site**
with a **vendor name** you'll recognize in the Regulatory Scraping list, pointing
at your hosted `index.html`.

## Test steps

### Part 1 — new file appears for review
1. Deploy the site (v1 live).
2. Run the scraper against it.
3. In the portal → **Regulatory Scraping** list, confirm the file registered as
   **Pending Review**.

### Part 2a — reopen on content change (NOT strictly rejected)
1. **Reject** the file (leave *Strictly Reject* **unchecked**).
2. Update content: copy `policy-v2.pdf` over `policy.pdf` (same name/URL) and
   redeploy.
   ```bash
   cp policy-v2.pdf policy.pdf   # then push / redeploy
   ```
3. Re-scrape.
4. ✅ Expected: status flips back to **Pending Review**
   (response: *"Content changed since this file was rejected; returned to Pending Review"*).

### Part 2b — stays rejected (Strictly Rejected)
1. Reset the live file to v1 (`cp policy-v1.pdf policy.pdf`, redeploy) and
   re-scrape so it's back to Pending Review, **or** use a second file.
2. **Reject** it with *Strictly Reject* **checked**.
3. Update content to v2 (as above) and re-scrape.
4. ✅ Expected: status **stays Rejected**
   (response: *"Content changed, but the file is Strictly Rejected; kept Rejected"*).

## Content hashes (for reference)

Re-generate anytime with `make_pdfs.py`. As generated:

- `policy-v1.pdf` → `6bdd51c0f65a493bb505a27301677f761ffb4d26b5240ff8f3211c25002d78a6`
- `policy-v2.pdf` → `eb82208d9a78dd9bc1fc172da14ffa0f76a1514866f020fc26ec6200d01396e5`

The two differ, which is what makes the re-scrape register as a content change.
