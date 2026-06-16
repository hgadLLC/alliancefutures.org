# Admin setup

The admin lives at https://alliancefutures.org/admin/ and lets you publish
TAFI content through web forms without touching code or Git.

It's a single static HTML page (`admin/index.html`) that calls the GitHub
API directly from your browser. Your access token stays in browser
localStorage — never transmitted anywhere except api.github.com.

## First-time setup

1. Open https://alliancefutures.org/admin/.
2. Click the GitHub token link on the sign-in screen. It opens a token
   creation page on github.com with the correct `repo` scope pre-selected
   and a sensible description.
3. Click "Generate token" at the bottom of GitHub's page, then copy the
   token (starts with `ghp_`).
4. Paste it back into the admin sign-in screen, click "Sign in".
5. Done. The token is now in your browser; you stay signed in until you
   click "Sign out" or clear browser data.

## What each form does

- **Add a Weekly Monitor** — composes a Week N markdown file, uploads the
  PDF and any theme figures, commits everything in one batch. A push
  triggers the GitHub Actions deploy.
- **Add a Commentary** — Southern Signals or other op-eds. Uploads PDF +
  hero image, writes `content/commentary/{slug}.md`.
- **Add a Team Member** — uploads the photo to `images/team/`, writes
  `content/people/{slug}.md`. (Prev/next nav links between bios still
  need to be wired manually after creating.)
- **Add to Recent Work (External)** — appends a new mention entry to
  `data/mentions.yml`. Shows up on the author's bio page.
- **Add to Recent Work (Internal)** — appends a TAFI publication entry to
  `data/internal-publications.yml`. Shows up on every listed author's
  bio page.

Anything not on a form (rename a role, fix a typo in body copy, change a
footer, edit the homepage) is still done by editing the relevant file on
GitHub directly — github.com/hgadLLC/alliancefutures.org.

## Why we built it this way

We tried hosted CMS options (Sveltia, Decap+Netlify). All of them
required a working OAuth bridge to GitHub, and our token-only fallback
flow never quite stuck. So we own the surface: one HTML file, one script,
no dependencies. If something breaks, it's all in `admin/index.html` —
readable in 15 minutes.
