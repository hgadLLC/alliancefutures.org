#!/usr/bin/env python3
"""Parse weekly PRC Pacific Embassies Monitor HTML files into Eleventy markdown.

Output: content/monitors/week-{N}.md with YAML frontmatter (week, date, date_end,
title, description, pdf, ambassadors_corner, summary, themes[]) and an empty body.

Run with: python3 tools/migrate_monitor_to_markdown.py
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "embassy-monitors"
OUT_DIR = ROOT / "content" / "monitors"

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May.": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sept": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def parse_date_range(text: str) -> tuple[date, date]:
    """Parse strings like 'Week 17 — June 1 – 7, 2026' or 'Week 18 — June 8, 2026 – Jun 14, 2026'."""
    t = (text.replace("&ndash;", "–").replace("&mdash;", "—")
          .replace("–", "–").replace("—", "—"))
    after_dash = t.split("—", 1)[1].strip() if "—" in t else t
    parts = after_dash.split("–")
    if len(parts) != 2:
        raise ValueError(f"Cannot split date range: {text!r}")
    left, right = parts[0].strip(), parts[1].strip()
    year_m = re.search(r"\b(20\d{2})\b", right)
    if not year_m:
        raise ValueError(f"No year in: {text!r}")
    year = int(year_m.group(1))
    right_no_year = right.replace(year_m.group(1), "").replace(",", "").strip()

    def parse_one(s: str, default_year: int, hint_month: str | None = None) -> date:
        s = s.replace(",", "").strip()
        m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})$", s)
        if m:
            mon = MONTHS[m.group(1)]
            return date(default_year, mon, int(m.group(2)))
        m = re.match(r"^(\d{1,2})$", s)
        if m and hint_month:
            return date(default_year, MONTHS[hint_month], int(m.group(1)))
        raise ValueError(f"Cannot parse date piece: {s!r}")

    left_month_m = re.match(r"^([A-Za-z]+)", left)
    hint = left_month_m.group(1) if left_month_m else None
    d1 = parse_one(left, year, hint)
    d2 = parse_one(right_no_year, year, hint)
    return d1, d2


def html_to_markdown(node: Tag) -> str:
    """Convert a single block-level element (p or li) into a markdown line, preserving links."""
    out: list[str] = []
    for child in node.children:
        if isinstance(child, NavigableString):
            out.append(str(child))
        elif isinstance(child, Tag):
            if child.name == "a":
                href = child.get("href", "")
                text = child.get_text()
                out.append(f"[{text}]({href})")
            elif child.name == "strong" or child.name == "b":
                out.append(f"**{child.get_text()}**")
            elif child.name == "em" or child.name == "i":
                out.append(f"*{child.get_text()}*")
            elif child.name == "br":
                out.append("\n")
            elif child.name == "sup":
                out.append(child.get_text())
            else:
                out.append(child.get_text())
    return "".join(out).strip()


def yaml_block(value: str, indent: int = 0) -> str:
    """Render a multiline string as a YAML block scalar with proper indent."""
    pad = " " * indent
    inner = " " * (indent + 2)
    body = value.replace("\r\n", "\n").strip("\n")
    lines = [f"{inner}{ln}" if ln else "" for ln in body.split("\n")]
    return "|\n" + "\n".join(lines)


def yaml_quote(value: str) -> str:
    """Quote a single-line value for YAML, escaping double quotes."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def localize_url(url: str) -> str:
    """Rewrite relative HTML hrefs to absolute /embassy-monitors/ paths."""
    if not url:
        return url
    if url.startswith("images/"):
        return "/embassy-monitors/" + url
    if url.startswith("pdfs/"):
        return "/embassy-monitors/" + url
    return url


def extract_paragraph_md(p: Tag) -> str:
    return html_to_markdown(p)


def parse_monitor(html_path: Path) -> dict:
    soup = BeautifulSoup(html_path.read_text(), "html.parser")
    article = soup.select_one("article.monitor-article")
    if not article:
        raise ValueError(f"No article in {html_path}")

    meta_date = article.select_one(".monitor-meta-date").get_text(strip=True)
    week_m = re.search(r"Week\s+(\d+)", meta_date)
    week = int(week_m.group(1))
    d1, d2 = parse_date_range(meta_date)

    pdf_a = article.select_one("a.monitor-download")
    pdf_href = pdf_a["href"] if pdf_a else None
    if pdf_href and not pdf_href.startswith("/"):
        pdf_href = "/embassy-monitors/" + pdf_href.lstrip("./")

    main_h2 = None
    for h2 in article.find_all("h2", recursive=False):
        if h2.get_text(strip=True) not in ("Summary of PRC Activity",):
            txt = h2.get_text(strip=True)
            if not txt.startswith("This Week"):
                main_h2 = h2
                break
    title = main_h2.get_text(strip=True) if main_h2 else f"Week {week} Monitor"

    ambassadors_corner = ""
    corner = article.select_one(".callout-box--float.callout-box--note")
    if corner:
        paras = [extract_paragraph_md(p) for p in corner.find_all("p", class_="callout-box__text")]
        ambassadors_corner = "\n\n".join(p for p in paras if p)

    desc_meta = soup.find("meta", attrs={"name": "description"})
    description = desc_meta.get("content", "") if desc_meta else ""

    children = list(article.children)
    nodes = [c for c in children if isinstance(c, Tag)]

    def idx_of_h2(text_pred):
        for i, n in enumerate(nodes):
            if n.name == "h2" and text_pred(n.get_text(strip=True)):
                return i
        return -1

    i_summary = idx_of_h2(lambda t: t == "Summary of PRC Activity")
    i_themes = idx_of_h2(lambda t: t.startswith("This Week"))
    if i_summary < 0 or i_themes < 0:
        raise ValueError(f"{html_path}: cannot locate Summary or Themes header")

    summary_paras = []
    for j in range(i_summary + 1, i_themes):
        n = nodes[j]
        if n.name == "p":
            summary_paras.append(extract_paragraph_md(n))
    summary = "\n\n".join(p for p in summary_paras if p)

    themes = []
    cur = None
    i = i_themes + 1
    while i < len(nodes):
        n = nodes[i]
        if n.name == "h3":
            if cur is not None:
                themes.append(cur)
            cur = {"title": n.get_text(strip=True), "body_paras": [], "figure": None,
                   "figure_caption": None, "figure_source_url": None, "figure_source_label": None,
                   "supporting_events": []}
        elif n.name == "figure" and cur is not None:
            img = n.find("img")
            if img:
                cur["figure"] = localize_url(img.get("src", ""))
            cap = n.find("figcaption")
            if cap:
                src_a = None
                for a in cap.find_all("a"):
                    src_a = a
                if src_a:
                    cur["figure_source_url"] = src_a.get("href", "")
                    cur["figure_source_label"] = src_a.get_text(strip=True)
                    src_a.extract()
                cap_text = cap.get_text(" ", strip=True)
                cap_text = re.sub(r"\s*\(Source:\s*\)\s*$", "", cap_text).strip()
                cur["figure_caption"] = cap_text
        elif n.name == "p" and cur is not None:
            text = extract_paragraph_md(n)
            if text == "**Supporting Events**":
                pass
            else:
                cur["body_paras"].append(text)
        elif n.name == "ul" and cur is not None:
            for li in n.find_all("li", recursive=False):
                country = ""
                strong = li.find("strong")
                if strong:
                    country = strong.get_text(strip=True).rstrip(":").strip()
                    strong.extract()
                a = li.find("a")
                if a:
                    label = a.get_text(strip=True)
                    url = a.get("href", "")
                    cur["supporting_events"].append({"country": country, "label": label, "url": url})
        elif n.name in ("div", "nav"):
            classes = n.get("class") or []
            if "monitor-endnote" in classes or "monitor-nav" in classes:
                break
        i += 1
    if cur is not None:
        themes.append(cur)

    prev_week = None
    next_week = None
    nav_el = article.select_one("nav.monitor-nav")
    if nav_el:
        for a in nav_el.find_all("a"):
            href = a.get("href", "")
            mp = re.match(r"week-(\d+)\.html", href)
            if not mp:
                continue
            text = a.get_text(strip=True)
            if "Previous" in text or "←" in text or "&larr" in text:
                prev_week = int(mp.group(1))
            elif "Next" in text or "→" in text or "&rarr" in text:
                next_week = int(mp.group(1))

    return {
        "week": week,
        "date": d1.isoformat(),
        "date_end": d2.isoformat(),
        "title": title,
        "description": description,
        "pdf": pdf_href,
        "prev_week": prev_week,
        "next_week": next_week,
        "ambassadors_corner": ambassadors_corner,
        "summary": summary,
        "themes": themes,
    }


def render_markdown(data: dict) -> str:
    lines = ["---"]
    lines.append("layout: layouts/monitor.njk")
    lines.append(f"week: {data['week']}")
    lines.append(f"date: {data['date']}")
    lines.append(f"date_end: {data['date_end']}")
    lines.append(f"title: {yaml_quote(data['title'])}")
    if data.get("description"):
        lines.append(f"description: {yaml_quote(data['description'])}")
    if data.get("pdf"):
        lines.append(f"pdf: {data['pdf']}")
    if data.get("prev_week"):
        lines.append(f"prev_week: {data['prev_week']}")
    if data.get("next_week"):
        lines.append(f"next_week: {data['next_week']}")
    lines.append("authors: [jonah-bock]")
    lines.append("categories: [embassies-monitor]")
    lines.append("featured: false")
    if data.get("ambassadors_corner"):
        lines.append("ambassadors_corner: " + yaml_block(data["ambassadors_corner"], indent=0))
    if data.get("summary"):
        lines.append("summary: " + yaml_block(data["summary"], indent=0))
    if data.get("themes"):
        lines.append("themes:")
        for t in data["themes"]:
            lines.append(f"  - title: {yaml_quote(t['title'])}")
            if t.get("body_paras"):
                lines.append("    body: " + yaml_block("\n\n".join(t["body_paras"]), indent=4))
            if t.get("figure"):
                lines.append(f"    figure: {t['figure']}")
            if t.get("figure_caption"):
                lines.append(f"    figure_caption: {yaml_quote(t['figure_caption'])}")
            if t.get("figure_source_url"):
                lines.append(f"    figure_source_url: {t['figure_source_url']}")
            if t.get("figure_source_label"):
                lines.append(f"    figure_source_label: {yaml_quote(t['figure_source_label'])}")
            if t.get("supporting_events"):
                lines.append("    supporting_events:")
                for ev in t["supporting_events"]:
                    lines.append(f"      - country: {yaml_quote(ev['country'])}")
                    lines.append(f"        label: {yaml_quote(ev['label'])}")
                    lines.append(f"        url: {ev['url']}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC_DIR.glob("week-*.html"), key=lambda p: int(re.search(r"week-(\d+)", p.name).group(1)))
    target_weeks = [int(w) for w in sys.argv[1:]] if len(sys.argv) > 1 else None
    written = 0
    skipped = 0
    for f in files:
        wn = int(re.search(r"week-(\d+)", f.name).group(1))
        if target_weeks and wn not in target_weeks:
            continue
        if wn == 18:
            print(f"week-{wn}: skipped (already hand-authored)")
            skipped += 1
            continue
        try:
            data = parse_monitor(f)
        except Exception as e:
            print(f"week-{wn}: PARSE FAILED — {e}")
            continue
        out = OUT_DIR / f"week-{wn}.md"
        out.write_text(render_markdown(data))
        print(f"week-{wn}: wrote {out.relative_to(ROOT)}")
        written += 1
    print(f"\nWrote {written} files, skipped {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
