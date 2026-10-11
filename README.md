# trinitytaxri.com

Static site for Trinity Tax Group, hosted on GitHub Pages. The form sends to your business email through Formspree.

## Files

- `content.md`: all the site's text, fees, and form questions. **Edit this file.**
- `build.py`: turns content.md into index.html
- `index.html`: the home page, generated from content.md (don't edit by hand)
- `privacy.html`: privacy notice linked in the footer
- `styles.css`: all styling
- `assets/`: logo, favicon, headshot
- `CNAME`: tells GitHub Pages to serve the site at trinitytaxri.com

## 1. Set up the form (Formspree)

1. Create a free account at formspree.io using ryan@trinitytaxri.com. Submissions go to the account email, so nothing in the site code needs your address.
2. Create a new form. Copy its ID (the part after `/f/` in the endpoint, e.g. `xayzabcd`).
3. In `content.md`, replace `YOUR_FORM_ID` on the "Formspree ID" line, then re-render.
4. After the site is live, submit a test request and confirm the email arrives (Formspree asks you to confirm the first one).
5. In Formspree's form settings, restrict submissions to `trinitytaxri.com` so other sites can't post to your form.

The free plan allows 50 submissions a month.

## 2. Publish on GitHub Pages

1. Create a public repository on GitHub (e.g. `trinitytaxri.com`).
2. Upload everything in this folder to the root of the repository, keeping the `assets` folder.
3. Go to Settings > Pages. Under "Build and deployment," choose "Deploy from a branch," branch `main`, folder `/ (root)`. Save.
4. Under "Custom domain," enter `trinitytaxri.com` and save.

## 3. Point the domain at GitHub (at your registrar)

Add these DNS records:

| Type  | Host / Name | Value                      |
|-------|-------------|----------------------------|
| A     | @           | 185.199.108.153            |
| A     | @           | 185.199.109.153            |
| A     | @           | 185.199.110.153            |
| A     | @           | 185.199.111.153            |
| CNAME | www         | YOUR-GITHUB-USERNAME.github.io |

Remove any parking-page A records or URL forwarding the registrar added by default.

Leave your email records alone. The MX and TXT (SPF/DKIM) records that deliver mail to ryan@trinitytaxri.com are separate from the A and CNAME records above, and deleting them stops your email, including form submissions.

DNS can take up to a day. Once GitHub shows the domain as verified, check "Enforce HTTPS" in Settings > Pages.

Recommended: verify the domain under your GitHub account settings (Settings > Pages > Add a domain) so no one else can claim it on GitHub.

## Editing later

1. Edit `content.md`.
2. Ask Claude to re-render, or run `python3 build.py` in this folder.
3. Upload the new `index.html` to the repository. The site updates within a minute or two.

Uploading `content.md` and `build.py` to GitHub is optional. They're harmless there and keep everything in one place.
