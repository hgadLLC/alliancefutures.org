# Admin / CMS rollout plan

Authoring through `/admin/` requires four phases. **Phases 1–3 are done.**
Phase 4 is staged but waits on a one-time GitHub Settings change before
it takes effect.

## Phase 1 — scaffold ✅

- `package.json` + `.eleventy.js` so Eleventy can build from `content/`
- `admin/index.html` (Decap CMS shell, SRI-pinned)
- `admin/config.yml` (initial: `monitors` + `people` collections)
- `admin/SETUP.md` (Netlify Identity + Git Gateway one-time setup)
- `.gitignore` updated for `node_modules/` + `_site/`

Nothing in the live site changes. `/admin/` is reachable but rejects logins
until the user finishes the Netlify setup in `admin/SETUP.md`.

## Phase 2 — content migration ✅

Convert every hand-built HTML page into a markdown file under `content/`,
with a layout template that renders the equivalent HTML.

**Status:**

- All 18 weekly monitors (incl. Week 16 Special Report) → `content/monitors/`
- 3 Southern Signals commentaries → `content/commentary/`
- 2 Red Team reports (Ukraine, PICs) → `content/research/`
- 9 bios (incl. Marc Ablong) → `content/people/`
- 5 layouts written: `base.njk`, `monitor.njk`, `special-report.njk`,
  `commentary.njk`, `red-team.njk`, `bio.njk`
- 4 migration scripts under `tools/` (monitor, special report, commentary,
  red team, bios)
- Inline CSS extracted to `css/monitor.css`, `css/commentary.css`,
  `css/red-team.css`
- Static pages (about, advisory, support, privacy), listing pages, and the
  homepage are passthrough-copied for now — they still ship in `_site/`
  but aren't yet CMS-editable. Phase 5 can revisit if needed.

Targets:

| Source                                        | Target                                                  | Count |
| ---                                           | ---                                                     | ---   |
| `embassy-monitors/week-N.html` (regular)      | `content/monitors/week-N.md` (layout: monitor)          | 17    |
| `embassy-monitors/week-16.html` (special)     | `content/monitors/week-16.md` (layout: special-report)  | 1     |
| `publications/ukraine-red-team.html`          | `content/research/ukraine-red-team.md` (layout: red-team) | 1   |
| `publications/pics-red-team.html`             | `content/research/pics-red-team.md` (layout: red-team)  | 1     |
| `our-work/commentary/*.html`                  | `content/commentary/*.md` (layout: commentary)          | 3     |
| `team/*.html`                                 | `content/people/*.md` (layout: bio)                     | 9     |
| `index.html`, `about.html`, `advisory.html`,  | `content/pages/*.md` + `content/homepage.yml`           | 5     |
| `support.html`, `privacy.html`                | (one per page)                                          |       |
| Listing pages (Our Work hub, category pages,  | Built from collections by templates                     | 6     |
| Embassies Monitor landing, People)            | (no markdown source — fully derived)                    |       |

Approach:

1. Write a one-off `tools/migrate_to_markdown.py` that:
   - Reads each HTML file
   - Extracts structured fields (title, date, hero image, themes, supporting
     events, ambassador's corner, etc.) using regex + light HTML parsing
   - Emits the equivalent markdown with frontmatter
2. Build the five layout templates in `_includes/layouts/`:
   - `base.njk` — head, nav, footer
   - `monitor.njk`
   - `special-report.njk`
   - `commentary.njk`
   - `red-team.njk`
   - `bio.njk`
3. Run `npm run build`, diff `_site/` against the live HTML, hand-clean any
   drift.

Live deploy still untouched.

## Phase 3 — expand CMS config ✅

Collections shipped in `admin/config.yml`:

- **Special Reports** (separate collection from weekly monitors, different
  layout fields: cover, Key Findings list, free-form sections)
- **Commentary** (with `series` select: Southern Signals, etc.)
- **Red-Team Reports** (cover, TOC anchors, scenarios with embedded memos,
  acknowledgements)
- **Homepage** (hero copy, featured pieces, channel cards, mission section)
- **Pages** (about, advisory, support, privacy — each as a single editable
  entry with body markdown + structured intro fields)
- **Site settings** (footer copy, contact emails — pulled from
  `content/site.yml` and surfaced as a single editable entry)

Test by editing one piece of every type through `/admin/` and confirming the
Eleventy output is correct.

## Phase 4 — cutover (staged, awaiting one manual step)

1. ✅ `.github/workflows/deploy.yml` — builds Eleventy and deploys
   `_site/` to GitHub Pages via the official `actions/deploy-pages` action.
2. **YOU DO THIS ONCE:** GitHub repo → Settings → Pages → Source: change
   from "Deploy from a branch" to **"GitHub Actions"**. That single switch
   tells Pages to serve from the workflow's artifact instead of the
   `main` branch root.
3. Push to `main` triggers the workflow. The new HTML appears at
   alliancefutures.org within a minute or two.
4. After confirming the cutover is clean (a week of normal editing), delete
   the hand-built HTML files at the repo root (`index.html`, `about.html`,
   `embassy-monitors/*.html`, `publications/*.html`, `our-work/**/*.html`,
   `team/*.html`). The CMS-authored markdown becomes the canonical source.
   Until then, those files keep flowing through via passthrough so nothing
   on the live site changes.

After Phase 4, every editing task is done through `/admin/`:

- Add a weekly monitor → CMS → markdown → rebuilds the issue page +
  Embassies Monitor landing + homepage feed + author bio's Recent Work
- Add a commentary → same flow, posts to Commentary landing, homepage feed,
  author bio
- Add a team member → CMS → markdown → people.html card + dedicated bio page
  + homepage People preview row
- Rename a role title (e.g. "Associate Director" → "Deputy Director") →
  one field edit; rebuilds everywhere
- Pin/unpin a piece as Featured → one boolean toggle
- Edit footer copy / channel cards / hero text → CMS field edits

Nothing touches HTML.
