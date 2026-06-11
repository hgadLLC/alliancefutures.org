# Publishing workflow

This site keeps a single source of truth for everything we publish, and a
build script that regenerates every list, count, and bio that mentions it.

## Source of truth

`data/internal-publications.yml` &mdash; one YAML entry per published piece.
A minimal entry:

```yaml
- type: monitor           # monitor | monitor-special | redteam | commentary | brief
  title: "Wale Goes to Canberra; Beijing Stays Busy"
  outlet: PRC Pacific Embassies Monitor &middot; Wk 17
  date: 2026-06-01
  url: embassy-monitors/week-17.html      # path from repo root
  authors: [jonah-bock]                   # one or more team/<slug>.html slugs
  category: embassies-monitor             # primary category
  product_type: Embassies Monitor
  region: Pacific
  countries: [Solomon Islands, Tonga]
  excerpt: "One-line dek shown on cards and bios."
```

Optional fields:

| field         | what it does                                                                 |
| ------------- | ---------------------------------------------------------------------------- |
| `also_in`     | List of additional category slugs (e.g. `[research]` for cross-listing).    |
| `featured`    | `true` pins the piece to the top of the homepage feed + category landings.  |
| `tag_class`   | Override the card pill style (e.g. `is-southern-signals`, `is-research`).   |
| `image`       | Thumbnail path (relative to repo root). Defaults to the category default.   |
| `series`      | Display name of a series (e.g. `Southern Signals`).                          |

Strings should be written as they will appear in HTML &mdash; use entities like
`&rsquo;`, `&mdash;`, `&ndash;` rather than raw curly punctuation.

## Build script

```bash
python3 tools/build_our_work.py
```

Reads the YAML and writes:

1. `data/work.json` &mdash; derived JSON snapshot.
2. `our-work/index.html` &mdash; the Our Work hub (category cards + counts).
3. `our-work/research.html`, `futures.html`, `commentary.html` &mdash; category
   landings with horizontal-bar cards and rail counts.
4. `embassy-monitors/index.html` &mdash; the Embassies Monitor landing.
5. `index.html` &mdash; the homepage "What We're Publishing" feed.
6. `team/<slug>.html` &mdash; the Recent Work block inside every bio that has
   the auto-management markers (see below).

Re-running is safe and idempotent.

## Bio Recent Work markers

Bio pages auto-render their Recent Work list from the YAML if they wrap the
managed block with:

```html
<h2>Recent Work</h2>
<!-- BEGIN:bio-recent-work author="jonah-bock" -->
<div class="recent-work-list">
    ...auto-managed items...
</div>
<button type="button" class="rw-toggle" ...>...</button>
<!-- END:bio-recent-work -->
```

The script regenerates everything between BEGIN and END:

- Filters `data/internal-publications.yml` for entries where the bio's slug
  appears in `authors`.
- Sorts newest first.
- Shows the first 5 items by default; collapses the rest behind a
  "Show N more" toggle (only emitted when there are more than 5 items).
- Empty author &rarr; renders a "No published TAFI work yet." placeholder.

External pieces (op-eds, In The Media) should live **outside** the markers and
stay manual &mdash; they are not part of the auto-managed TAFI corpus.

Currently auto-managed bios: `jonah-bock`, `andrew-horton`. The other bios
(`eric-lies`, `greg-brown`, `austin-wu`, `marc-ablong`) keep manual Recent
Work for now; add markers + an entry in the YAML to migrate one.

## Typical workflow: adding a new piece

1. Add the entry to `data/internal-publications.yml`. Drop it in the right
   section (Monitors, Red Team, Commentary, etc.). Position within the
   section doesn't matter &mdash; the script sorts by date.
2. Run `python3 tools/build_our_work.py`.
3. `git add -A && git commit && git push`.

The script outputs every file it changed, so the resulting diff should be
exactly the set of pages where the new piece needs to surface.
