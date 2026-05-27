# TAFI mentions automation

The "Recent Work" section that appears at the bottom of every team
bio page is generated automatically from two YAML files in this
folder. Adding a new mention takes about 30 seconds.

## Files

- **`mentions.yml`** — external commentary, op-eds, podcasts, panel
  appearances, and media quotes published *outside* of TAFI.
- **`internal-publications.yml`** — TAFI's own published work
  (Embassies Monitor weeks, red-team reports, briefs, commentary).

Both files are read by the build script and merged per author.

## Adding a mention

1. Open `data/mentions.yml`.
2. Prepend a new entry at the top of the list (newest first):
   ```yaml
   - author: greg-brown
     type: commentary
     title: How Australia is rethinking AUKUS
     outlet: The Strategist
     date: 2026-04-15
     url: https://aspistrategist.org.au/...
     excerpt: Optional one-line dek.
   ```
3. From the project root, run:
   ```
   python3 team/_build_bios.py
   ```
4. Verify the bio renders correctly (`team/<slug>.html`).
5. Commit `data/mentions.yml` plus the regenerated `team/*.html`
   files.

## Adding an internal publication

Same workflow with `data/internal-publications.yml`. Note the
`authors` field is a list — a single piece can credit multiple
people, and it'll show on each of their bio pages.

```yaml
- type: report
  title: Pacific Islands Red Team Event Report
  outlet: TAFI Red Team Report
  date: 2026-03-01
  url: publications/pics-red-team.html      # path from project root
  authors: [greg-brown, eric-lies]
  excerpt: A structured analytic exercise…
```

## Author slugs

These match the filenames in `team/`:

| Person                | Slug                  |
|-----------------------|-----------------------|
| Dr. Greg Brown        | `greg-brown`          |
| Eric Lies             | `eric-lies`           |
| Jonah Bock            | `jonah-bock`          |
| Leah Markworth        | `leah-markworth`      |
| Dr. Nishank Motwani   | `nishank-motwani`     |
| Jackie Gibson         | `jackie-gibson`       |
| Austin Wu             | `austin-wu`           |

## Type values

Used to render the small-caps tag on each item.

| Value         | Renders as          |
|---------------|---------------------|
| `monitor`     | EMBASSIES MONITOR   |
| `redteam`     | RED TEAM REPORT     |
| `report`      | REPORT              |
| `brief`       | BRIEF               |
| `book`        | BOOK / EDITED VOLUME|
| `chapter`     | BOOK CHAPTER        |
| `commentary`  | COMMENTARY          |
| `op-ed`       | OP-ED               |
| `media`       | IN THE MEDIA        |
| `interview`   | INTERVIEW           |
| `podcast`     | PODCAST             |
| `panel`       | PANEL               |
| `citation`    | CITATION            |

To add a new type, edit `TYPE_LABELS` in
[`../team/_build_bios.py`](../team/_build_bios.py).

## What the build script does

1. Reads both YAML files.
2. For each person in `PEOPLE` (defined in `_build_bios.py`):
   - Filters `mentions.yml` entries by `author == slug`.
   - Filters `internal-publications.yml` entries by `slug in authors`.
   - Sorts by date descending, caps at 10 items.
   - Renders a "Recent Work" section in their bio.
3. Writes `team/<slug>.html` for every person.

Empty result is fine — the section is omitted if a person has
no items yet.

## Future: web form for editors

When editors want a no-terminal flow, we can add Decap CMS at
`/admin/index.html` pointing at these two YAML files. It runs in
the browser, authenticates via GitHub OAuth, and commits to the
repo on save. Build runs server-side via GitHub Actions.

That's a ~30-minute setup; defer until manual editing becomes a
chore.
