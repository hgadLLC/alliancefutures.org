#!/usr/bin/env python3
"""Generator for TAFI Our Work + Embassies Monitor landing pages
and the homepage "What We're Publishing" feed.

Reads data/internal-publications.yml, sorts (featured first then date desc),
and writes:

  1. data/work.json                  - canonical JSON
  2. our-work/index.html             - Our Work hub (4 category cards)
  3. our-work/research.html          - Research category landing
  4. our-work/futures.html           - Futures category landing
  5. our-work/commentary.html        - Commentary category landing
  6. embassy-monitors/index.html     - Embassies Monitor landing (regenerated
                                       cards in horizontal-bar style)
  7. Patches index.html homepage feed to use the same horizontal-bar style

All Our Work pages share css/our-work.css and a right-rail category nav.
Pin a piece to the top of the homepage feed + landings: set featured: true
in the YAML entry.

Usage:  python3 tools/build_our_work.py
"""
import datetime
import html
import json
import pathlib
import re
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBS_YAML = ROOT / "data" / "internal-publications.yml"
WORK_JSON = ROOT / "data" / "work.json"
OUR_WORK_DIR = ROOT / "our-work"
EMBASSY_HUB = ROOT / "embassy-monitors" / "index.html"
INDEX_HTML = ROOT / "index.html"

CONTRIBUTOR_TYPE = {
    "greg-brown": "staff",
    "eric-lies": "staff",
    "jonah-bock": "staff",
    "leah-markworth": "staff",
    "nishank-motwani": "fellow",
    "andrew-horton": "fellow",
    "austin-wu": "fellow",
    "jackie-gibson": "fellow",
}

AUTHOR_NAME = {
    "greg-brown": "Dr. Greg Brown",
    "eric-lies": "Eric Lies",
    "jonah-bock": "Jonah Bock",
    "leah-markworth": "Leah Markworth",
    "nishank-motwani": "Dr. Nishank Motwani",
    "andrew-horton": "Andrew Horton",
    "austin-wu": "Austin Wu",
    "jackie-gibson": "Jackie Gibson",
}

CATEGORY_LABEL = {
    "research": "Research",
    "futures": "Futures",
    "commentary": "Commentary",
    "embassies-monitor": "Embassies Monitor",
}

CATEGORY_BLURB = {
    "research": "Structured analytic reports, red-team exercises, and deep-dive studies.",
    "futures": "Scenario work and strategic-foresight pieces.",
    "commentary": "Op-eds, articles, and short commentary.",
    "embassies-monitor": "Weekly open-source tracking of PRC diplomatic activity in the Pacific Islands.",
}

# Default thumbnail per category. Each YAML entry may override with image:
CATEGORY_IMAGE = {
    "research": "images/publications-hero.jpg",
    "futures": "images/hero.jpg",
    "commentary": "images/about-study.jpg",
    "embassies-monitor": "images/monitor-hero.jpg",
}

# Per-week thumbnails for Embassies Monitor entries are auto-discovered
# from embassy-monitors/images/thumbs/week-N.jpg. The YAML doesn't have
# to spell them out — if a thumb exists for the week number, it wins
# over the category default.
EM_THUMB_DIR = ROOT / "embassy-monitors" / "images" / "thumbs"
EM_WEEK_RE = re.compile(r"embassy-monitors/week-(\d+)\.html")


def lookup_em_thumb(url):
    m = EM_WEEK_RE.search(url or "")
    if not m:
        return None
    candidate = EM_THUMB_DIR / f"week-{m.group(1)}.jpg"
    if candidate.exists():
        return f"embassy-monitors/images/thumbs/week-{m.group(1)}.jpg"
    return None

HOMEPAGE_FEED_LIMIT = 6


def iso(d):
    if isinstance(d, datetime.date):
        return d.isoformat()
    return str(d) if d else ""


def date_pretty(s):
    try:
        return datetime.date.fromisoformat(s).strftime("%b %-d, %Y")
    except Exception:
        return s or ""


def normalize(items):
    out = []
    for it in items:
        slugs = it.get("authors") or []
        ctypes = sorted({CONTRIBUTOR_TYPE.get(s, "guest") for s in slugs})
        cat = it.get("category")
        if not cat:
            t = it.get("type", "")
            cat = "embassies-monitor" if t == "monitor" else (
                "research" if t == "redteam" else "commentary"
            )
        author_names = [AUTHOR_NAME.get(s, s.replace("-", " ").title()) for s in slugs]
        image = it.get("image") or lookup_em_thumb(it.get("url", "")) or CATEGORY_IMAGE.get(cat, "images/hero.jpg")
        out.append({
            "title": it.get("title", ""),
            "outlet": it.get("outlet", ""),
            "type": it.get("type", ""),
            "category": cat,
            "category_label": CATEGORY_LABEL.get(cat, cat.title()),
            "product_type": it.get("product_type", ""),
            "region": it.get("region", ""),
            "countries": it.get("countries") or [],
            "authors": slugs,
            "author_names": author_names,
            "contributor_types": ctypes,
            "date": iso(it.get("date")),
            "date_pretty": date_pretty(iso(it.get("date"))),
            "url": it.get("url", "#"),
            "image": image,
            "featured": bool(it.get("featured", False)),
            "excerpt": it.get("excerpt", ""),
        })
    out.sort(key=lambda x: x["date"], reverse=True)
    out.sort(key=lambda x: 0 if x["featured"] else 1)
    return out


# ----- Horizontal-bar card HTML -----

def render_bar(it, url_prefix="../"):
    """Render a single horizontal-bar card. url_prefix='' for root pages."""
    is_research = it["type"] in ("redteam", "report", "brief")
    tag_class = " is-research" if is_research else ""
    outlet = it["outlet"] or it.get("product_type") or it["category_label"]
    image = it["image"]
    if not image.startswith("http"):
        if url_prefix == "" and image.startswith("../"):
            image = image[3:]  # strip the "../" since we're at root
        elif url_prefix == "../" and not image.startswith("../") and not image.startswith("/"):
            image = "../" + image
    pin = '<span class="ow-bar-pin">&#9733; Featured</span>' if it["featured"] else ""
    href = url_prefix + it["url"] if url_prefix else it["url"]
    authors = it["author_names"]
    if authors:
        authors_html = (
            f'<div class="ow-bar-authors">By <span>'
            + ", ".join(html.escape(a) for a in authors)
            + "</span></div>"
        )
    else:
        authors_html = ""
    return (
        f'                <a href="{href}" class="ow-bar">\n'
        f'                    <div class="ow-bar-img"><img src="{image}" alt="" loading="lazy"></div>\n'
        f'                    <div class="ow-bar-body">\n'
        f'                        <div class="ow-bar-meta">\n'
        f'                            <span class="ow-bar-tag{tag_class}">{outlet}</span>\n'
        f'                            {pin}\n'
        f'                            <span class="ow-bar-date">{html.escape(it["date_pretty"])}</span>\n'
        f'                        </div>\n'
        f'                        <h3 class="ow-bar-title">{it["title"]}</h3>\n'
        f'                        <p class="ow-bar-excerpt">{it["excerpt"]}</p>\n'
        f'                        {authors_html}\n'
        f'                    </div>\n'
        f'                    <span class="ow-bar-arrow">Read &rarr;</span>\n'
        f'                </a>'
    )


def render_bars(items, url_prefix="../"):
    if not items:
        return ""
    return "\n\n".join(render_bar(it, url_prefix) for it in items)


# ----- Right rail -----

def render_rail(items, active_category, url_prefix="../"):
    """Render the sticky right-side category rail.
    active_category: research | futures | commentary | embassies-monitor | None (hub)
    """
    counts = {}
    for it in items:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    rows = []
    for slug in ("research", "futures", "commentary", "embassies-monitor"):
        if slug == "embassies-monitor":
            href = f"{url_prefix}embassy-monitors/index.html"
        else:
            href = f"{url_prefix}our-work/{slug}.html"
        active_cls = " is-active" if active_category == slug else ""
        n = counts.get(slug, 0)
        count_html = (
            f'<span class="ow-rail-count">{n} piece{"" if n == 1 else "s"}</span>'
            if n > 0
            else '<span class="ow-rail-count">Coming soon</span>'
        )
        rows.append(
            f'                <li>\n'
            f'                    <a href="{href}" class="ow-rail-link{active_cls}">\n'
            f'                        {CATEGORY_LABEL[slug]}\n'
            f'                        {count_html}\n'
            f'                    </a>\n'
            f'                </li>'
        )
    return (
        '        <aside class="ow-rail" aria-label="Categories">\n'
        '            <h4>Browse work</h4>\n'
        '            <ul class="ow-rail-list">\n'
        + "\n".join(rows)
        + '\n            </ul>\n'
        '        </aside>'
    )


# ----- Shared nav blocks -----

NAV_NESTED = """        <a href="../index.html" class="logo">
            <img src="../images/tafi-logo-real.png" alt="TAFI Logo" class="logo-img">
            <div class="logo-text">
                <span class="logo-text-main">TAFI</span>
                <span class="logo-text-sub">The Alliance Futures Initiative</span>
            </div>
        </a>
        <nav>
            <a href="../about.html">About</a>
            <div class="nav-dropdown">
                <a href="../our-work/index.html" class="nav-dropdown-trigger">Our Work <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
                <div class="nav-dropdown-menu">
                    <a href="../our-work/research.html">Research</a>
                    <a href="../our-work/futures.html">Futures</a>
                    <a href="../our-work/commentary.html">Commentary</a>
                    <a href="../embassy-monitors/index.html">Embassies Monitor</a>
                </div>
            </div>
            <a href="../advisory.html">Advisory</a>
            <a href="../people.html">People</a>
            <a href="../support.html">Support</a>
        </nav>
        <div class="mobile-menu"><span></span><span></span><span></span></div>
        <nav class="mobile-nav">
            <a href="../about.html">About</a>
            <div class="mobile-nav-group">
                <button class="mobile-nav-group-trigger">Our Work <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
                <div class="mobile-nav-group-items">
                    <a href="../our-work/research.html">Research</a>
                    <a href="../our-work/futures.html">Futures</a>
                    <a href="../our-work/commentary.html">Commentary</a>
                    <a href="../embassy-monitors/index.html">Embassies Monitor</a>
                </div>
            </div>
            <a href="../advisory.html">Advisory</a>
            <a href="../people.html">People</a>
            <a href="../support.html">Support</a>
        </nav>"""

FOOTER = """        <div class="container">
            <div class="footer-content">
                <div class="footer-logo">
                    <img src="../images/tafi-logo-real.png" alt="TAFI">
                    <span class="footer-logo-text">TAFI</span>
                </div>
                <div class="footer-links">
                    <a href="../about.html">About</a>
                    <a href="../our-work/index.html">Our Work</a>
                    <a href="../advisory.html">Advisory</a>
                    <a href="../people.html">People</a>
                    <a href="../support.html">Support</a>
                    <a href="../index.html#contact">Contact</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p style="max-width: 900px; margin: 0 auto 1rem; font-size: 0.85rem; line-height: 1.7;">
                    TAFI is supported by foundation grants, individual donors, and commercial advisory work, with a strict firewall between commercial engagements and our public research.
                </p>
                <p style="max-width: 900px; margin: 0 auto 1rem; font-size: 0.8rem; line-height: 1.7; opacity: 0.85;">
                    The Alliance Futures Initiative is a research program of OTX International, an independent, non-partisan 501(c)(3) public charity. Contributions are tax-deductible to the fullest extent permitted by law.
                </p>
                <p style="font-size: 0.8rem; opacity: 0.8;">
                    <a href="mailto:contact@alliancefutures.org" style="color: var(--ocean-light);">contact@alliancefutures.org</a>
                </p>
                <p style="margin-top: 1rem;">&copy; 2026 The Alliance Futures Initiative &middot; Founded 2026 &middot; <a href="../privacy.html" style="color: var(--ocean-light);">Privacy</a></p>
            </div>
        </div>"""

PAGE_SCRIPT = """    <script>
        const header = document.getElementById('header');
        window.addEventListener('scroll', () => header.classList.toggle('scrolled', window.scrollY > 100));
        const mobileMenu = document.querySelector('.mobile-menu');
        const mobileNav = document.querySelector('.mobile-nav');
        if (mobileMenu && mobileNav) {
            mobileMenu.addEventListener('click', () => { mobileMenu.classList.toggle('active'); mobileNav.classList.toggle('active'); });
            document.querySelectorAll('.mobile-nav a').forEach(l => l.addEventListener('click', () => { mobileMenu.classList.remove('active'); mobileNav.classList.remove('active'); }));
            document.querySelectorAll('.mobile-nav-group-trigger').forEach(t => t.addEventListener('click', () => { t.classList.toggle('active'); t.nextElementSibling.classList.toggle('active'); }));
        }
    </script>"""


def page_shell(title, hero_html, body_inner, css_extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{title}">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../css/shared.css?v=4">
    <link rel="stylesheet" href="../css/our-work.css?v=1">
    {css_extra}
</head>
<body>
    <header id="header">{NAV_NESTED}</header>

{hero_html}

    <section class="ow-body">
        <div class="container">
            <div class="ow-layout">
                <main class="ow-main">
{body_inner}
                </main>
__RAIL__
            </div>
        </div>
    </section>

    <footer>
{FOOTER}
    </footer>

{PAGE_SCRIPT}
</body>
</html>
"""


def make_hero(eyebrow, title_html, blurb, breadcrumb_html):
    return f"""    <section class="ow-hero">
        <div class="container">
            <nav class="breadcrumb" style="margin-bottom: 1rem;">{breadcrumb_html}</nav>
            <div class="ow-hero-eyebrow">{eyebrow}</div>
            <h1>{title_html}</h1>
            <p>{blurb}</p>
        </div>
    </section>"""


def build_hub_page(items):
    """our-work/index.html - hub showing 4 category cards."""
    counts = {}
    for it in items:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    hero = make_hero(
        eyebrow="Our Work",
        title_html="Research, futures, &amp; <em>commentary</em>",
        blurb=("Research, futures analysis, commentary, and the weekly "
               "Embassies Monitor &mdash; the full archive of TAFI's public work."),
        breadcrumb_html='<a href="../index.html">Home</a> <span>/</span> <span>Our Work</span>',
    )
    cards = []
    for slug in ("research", "futures", "commentary", "embassies-monitor"):
        n = counts.get(slug, 0)
        href = (
            "../embassy-monitors/index.html" if slug == "embassies-monitor"
            else f"{slug}.html"
        )
        count_text = (
            f'{n} piece{"" if n == 1 else "s"}' if n > 0 else "Coming soon"
        )
        cards.append(
            f'                <a href="{href}" class="ow-hub-card">\n'
            f'                    <h3>{CATEGORY_LABEL[slug]}</h3>\n'
            f'                    <p>{CATEGORY_BLURB[slug]}</p>\n'
            f'                    <span class="ow-hub-count">{count_text}</span>\n'
            f'                </a>'
        )
    body = (
        '                    <div class="ow-hub-grid">\n'
        + "\n".join(cards)
        + "\n                    </div>"
    )
    rail = render_rail(items, None, "../")
    page = page_shell(
        "Our Work | TAFI",
        hero,
        body,
    ).replace("__RAIL__", rail)
    (OUR_WORK_DIR / "index.html").write_text(page)
    print(f"our-work/index.html: hub written ({sum(counts.values())} pieces across {sum(1 for v in counts.values() if v)} categories)")


def build_category_page(slug, items):
    """our-work/<slug>.html - category landing with horizontal bars."""
    cat_items = [it for it in items if it["category"] == slug]
    hero = make_hero(
        eyebrow="Our Work",
        title_html=f"<em>{CATEGORY_LABEL[slug]}</em>",
        blurb=CATEGORY_BLURB[slug],
        breadcrumb_html=(
            '<a href="../index.html">Home</a> <span>/</span> '
            '<a href="index.html">Our Work</a> <span>/</span> '
            f'<span>{CATEGORY_LABEL[slug]}</span>'
        ),
    )
    if cat_items:
        body = (
            '                    <div class="ow-bars">\n'
            + render_bars(cat_items, "../")
            + "\n                    </div>"
        )
    else:
        body = (
            '                    <div class="ow-empty">\n'
            f'                        <strong>{CATEGORY_LABEL[slug]} is on the way.</strong>\n'
            '                        New pieces in this category will appear here as we publish.\n'
            '                    </div>'
        )
    rail = render_rail(items, slug, "../")
    page = page_shell(
        f"{CATEGORY_LABEL[slug]} | TAFI",
        hero,
        body,
    ).replace("__RAIL__", rail)
    (OUR_WORK_DIR / f"{slug}.html").write_text(page)
    print(f"our-work/{slug}.html: written ({len(cat_items)} pieces)")


def build_embassy_monitor_hub(items):
    """embassy-monitors/index.html - same layout as category pages, but the
    hero references the longstanding Embassies Monitor branding/imagery.
    """
    cat_items = [it for it in items if it["category"] == "embassies-monitor"]
    hero = f"""    <section class="ow-hero" style="position: relative; overflow: hidden;">
        <div style="position: absolute; inset: 0; background-image: url('../images/monitor-hero.jpg'); background-size: cover; background-position: center;"></div>
        <div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(5, 22, 40, 0.94) 0%, rgba(5, 22, 40, 0.78) 50%, rgba(5, 22, 40, 0.45) 100%);"></div>
        <div class="container" style="position: relative; z-index: 2;">
            <nav class="breadcrumb" style="margin-bottom: 1rem;">
                <a href="../index.html">Home</a> <span>/</span>
                <a href="../our-work/index.html">Our Work</a> <span>/</span>
                <span>Embassies Monitor</span>
            </nav>
            <div class="ow-hero-eyebrow">Our Work / Embassies Monitor</div>
            <h1>PRC Pacific <em>Embassies Monitor</em></h1>
            <p>A weekly open-source intelligence product systematically tracking Beijing's public diplomatic activity across the nine Pacific Island Countries that host Chinese embassies.</p>
        </div>
    </section>"""
    if cat_items:
        body = (
            '                    <div class="ow-bars">\n'
            + render_bars(cat_items, "../")
            + "\n                    </div>"
        )
    else:
        body = (
            '                    <div class="ow-empty">\n'
            '                        <strong>No monitors published yet.</strong>\n'
            '                        New weekly editions will appear here.\n'
            '                    </div>'
        )
    rail = render_rail(items, "embassies-monitor", "../")
    page = page_shell(
        "Embassies Monitor | TAFI",
        hero,
        body,
    ).replace("__RAIL__", rail)
    EMBASSY_HUB.write_text(page)
    print(f"embassy-monitors/index.html: rebuilt ({len(cat_items)} weeks)")


# ----- Homepage What We're Publishing feed (root paths, no ../) -----

def render_homepage_feed(items, limit=HOMEPAGE_FEED_LIMIT):
    rows = []
    for it in items[:limit]:
        is_research = it["type"] in ("redteam", "report", "brief")
        tag_class = " is-research" if is_research else ""
        outlet = it["outlet"] or it.get("product_type") or it["category_label"]
        image = it["image"]
        # Strip ../ for root-level page
        if image.startswith("../"):
            image = image[3:]
        pin = '<span class="ow-bar-pin">&#9733; Featured</span>' if it["featured"] else ""
        authors_html = ""
        if it["author_names"]:
            authors_html = (
                '<div class="ow-bar-authors">By <span>'
                + ", ".join(html.escape(a) for a in it["author_names"])
                + '</span></div>'
            )
        rows.append(
            f'                <a href="{it["url"]}" class="ow-bar">\n'
            f'                    <div class="ow-bar-img"><img src="{image}" alt="" loading="lazy"></div>\n'
            f'                    <div class="ow-bar-body">\n'
            f'                        <div class="ow-bar-meta">\n'
            f'                            <span class="ow-bar-tag{tag_class}">{outlet}</span>\n'
            f'                            {pin}\n'
            f'                            <span class="ow-bar-date">{html.escape(it["date_pretty"])}</span>\n'
            f'                        </div>\n'
            f'                        <h3 class="ow-bar-title">{it["title"]}</h3>\n'
            f'                        <p class="ow-bar-excerpt">{it["excerpt"]}</p>\n'
            f'                        {authors_html}\n'
            f'                    </div>\n'
            f'                    <span class="ow-bar-arrow">Read &rarr;</span>\n'
            f'                </a>'
        )
    return "\n\n".join(rows)


def patch_homepage(items):
    src = INDEX_HTML.read_text()
    # Replace whole <div class="recent-feed">...</div> ... <div class="recent-footer">
    block_re = re.compile(
        r'<div class="recent-feed[^"]*">.*?</div>\s*\n\s*<div class="recent-footer">',
        re.DOTALL,
    )
    feed_html = render_homepage_feed(items)
    # Use the new ow-bars container for consistent horizontal bars
    new_block = (
        f'<div class="recent-feed ow-bars">\n'
        f'{feed_html}\n'
        f'            </div>\n'
        f'\n'
        f'            <div class="recent-footer">'
    )
    new, n = block_re.subn(new_block, src)
    if n != 1:
        raise SystemExit("Failed to patch homepage feed: marker not found.")
    # Inject the our-work.css link if not already present (idempotent)
    if "css/our-work.css" not in new:
        new = new.replace(
            '<link rel="stylesheet" href="css/shared.css">',
            '<link rel="stylesheet" href="css/shared.css">\n    <link rel="stylesheet" href="css/our-work.css?v=1">',
            1,
        )
    INDEX_HTML.write_text(new)
    print(f"index.html: regenerated \"What We're Publishing\" feed ({min(HOMEPAGE_FEED_LIMIT, len(items))} items, horizontal bars)")


def main():
    raw = yaml.safe_load(PUBS_YAML.read_text()) or []
    items = normalize(raw)
    WORK_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"data/work.json: {len(items)} items")

    OUR_WORK_DIR.mkdir(parents=True, exist_ok=True)
    build_hub_page(items)
    for slug in ("research", "futures", "commentary"):
        build_category_page(slug, items)
    build_embassy_monitor_hub(items)
    patch_homepage(items)


if __name__ == "__main__":
    main()
