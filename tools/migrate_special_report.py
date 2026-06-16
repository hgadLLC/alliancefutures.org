#!/usr/bin/env python3
"""Convert embassy-monitors/week-16.html (the Special Report) into a markdown file
under content/monitors/week-16.md with the special-report layout."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "embassy-monitors" / "week-16.html"
OUT = ROOT / "content" / "monitors" / "week-16.md"


def inline_md(node) -> str:
    out: list[str] = []
    for child in (node.children if isinstance(node, Tag) else [node]):
        if isinstance(child, NavigableString):
            out.append(str(child))
        elif isinstance(child, Tag):
            if child.name == "a":
                href = child.get("href", "")
                txt = inline_md(child)
                out.append(f"[{txt}]({href})")
            elif child.name in ("strong", "b"):
                out.append(f"**{inline_md(child)}**")
            elif child.name in ("em", "i"):
                out.append(f"*{inline_md(child)}*")
            elif child.name == "br":
                out.append("  \n")
            elif child.name == "sup":
                out.append(inline_md(child))
            else:
                out.append(inline_md(child))
    return "".join(out)


def block_md(node: Tag) -> str:
    if node.name == "p":
        cls = node.get("class") or []
        if "lede" in cls:
            return ""
        return inline_md(node).strip() + "\n"
    if node.name in ("h2", "h3", "h4"):
        level = int(node.name[1])
        return ("#" * level) + " " + inline_md(node).strip() + "\n"
    if node.name in ("ul", "ol"):
        bullet = "- " if node.name == "ul" else "1. "
        lines = []
        for li in node.find_all("li", recursive=False):
            text = inline_md(li).strip()
            lines.append(bullet + text)
        return "\n".join(lines) + "\n"
    if node.name == "figure":
        img = node.find("img")
        cap = node.find("figcaption")
        src = img.get("src", "") if img else ""
        if src.startswith("images/"):
            src = "/embassy-monitors/" + src
        alt = img.get("alt", "") if img else ""
        cap_md = inline_md(cap).strip() if cap else ""
        out = f"![{alt}]({src})"
        if cap_md:
            out += f"\n\n*{cap_md}*"
        return out + "\n"
    return ""


def yaml_quote(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    soup = BeautifulSoup(SRC.read_text(), "html.parser")
    article = soup.select_one("article.monitor-article")

    hero_h1 = soup.select_one(".page-hero h1")
    # Hero title is rendered with `| safe`, so keep inline HTML (em/strong) rather
    # than convert to markdown that wouldn't be re-rendered.
    hero_title = "".join(str(c) for c in hero_h1.children).strip() if hero_h1 else ""

    meta_date = article.select_one(".monitor-meta-date").get_text(strip=True)
    week_m = re.search(r"Week\s+(\d+)", meta_date)
    week = int(week_m.group(1))

    author_div = article.select_one(".monitor-meta-author")
    author = ""
    author_title = ""
    if author_div:
        t = author_div.get_text(strip=True)
        m = re.match(r"^By\s+(.+?),\s*(.+)$", t)
        if m:
            author, author_title = m.group(1), m.group(2)
        else:
            author = t.replace("By ", "").strip()

    pdf_a = article.select_one("a.monitor-download")
    pdf = pdf_a["href"] if pdf_a else None
    if pdf and not pdf.startswith("/"):
        pdf = "/embassy-monitors/" + pdf.lstrip("./")

    cover = article.select_one("figure.cover-figure img")
    cover_src = cover.get("src", "") if cover else ""
    if cover_src.startswith("images/"):
        cover_src = "/embassy-monitors/" + cover_src
    cover_alt = cover.get("alt", "") if cover else ""

    article_h2 = None
    for h2 in article.find_all("h2", recursive=False):
        article_h2 = h2
        break
    main_title = inline_md(article_h2).strip() if article_h2 else ""

    lede_p = article.select_one("p.lede")
    lede_md = ""
    if lede_p:
        strong = lede_p.find("strong")
        target = strong if strong else lede_p
        lede_md = inline_md(target).strip()

    article_children = list(article.children)
    body_parts: list[str] = []
    seen_lede = False
    for n in article_children:
        if not isinstance(n, Tag):
            continue
        cls = n.get("class") or []
        if n.name == "div" and "publication-header" in cls:
            continue
        if n.name == "div" and "monitor-meta" in cls:
            continue
        if n.name == "figure" and "cover-figure" in cls:
            continue
        if n.name == "span" and "special-tag" in cls:
            continue
        if n.name == "h2" and n is article_h2:
            continue
        if n.name == "p" and "lede" in cls:
            seen_lede = True
            continue
        if n.name == "div" and "monitor-endnote" in cls:
            break
        if n.name == "aside" and "support-cta" in cls:
            continue
        if n.name == "nav" and "monitor-nav" in cls:
            continue
        md = block_md(n)
        if md.strip():
            body_parts.append(md)

    body = "\n".join(body_parts)

    endnote = article.select_one(".monitor-endnote")
    disclaimer = ""
    photo_credit = ""
    if endnote:
        ems = endnote.find_all("em")
        for em in ems:
            txt = inline_md(em).strip()
            if "Disclaimer" in txt:
                disclaimer = txt
            elif "Photo Credit" in txt:
                photo_credit = txt

    nav_el = article.select_one("nav.monitor-nav")
    prev_w = next_w = None
    if nav_el:
        for a in nav_el.find_all("a"):
            mp = re.match(r"week-(\d+)\.html", a.get("href", ""))
            if not mp:
                continue
            t = a.get_text(strip=True)
            if "Previous" in t:
                prev_w = int(mp.group(1))
            elif "Next" in t:
                next_w = int(mp.group(1))

    fm = [
        "---",
        "layout: layouts/special-report.njk",
        f"week: {week}",
        "date: 2026-05-25",
        "date_end: 2026-05-31",
        f"title: {yaml_quote(main_title)}",
        f"hero_title: {yaml_quote(hero_title)}",
    ]
    desc_meta = soup.find("meta", attrs={"name": "description"})
    if desc_meta:
        fm.append(f"description: {yaml_quote(desc_meta.get('content',''))}")
    if pdf:
        fm.append(f"pdf: {pdf}")
    if cover_src:
        fm.append(f"cover_image: {cover_src}")
        if cover_alt:
            fm.append(f"cover_alt: {yaml_quote(cover_alt)}")
    if author:
        fm.append(f"author: {yaml_quote(author)}")
    if author_title:
        fm.append(f"author_title: {yaml_quote(author_title)}")
    if lede_md:
        fm.append(f"lede: {yaml_quote(lede_md)}")
    if prev_w:
        fm.append(f"prev_week: {prev_w}")
    if next_w:
        fm.append(f"next_week: {next_w}")
    fm.append("authors: [jonah-bock]")
    fm.append("categories: [embassies-monitor, special-report]")
    fm.append("featured: true")
    if disclaimer:
        fm.append(f"disclaimer: {yaml_quote(disclaimer)}")
    if photo_credit:
        fm.append(f"photo_credit: {yaml_quote(photo_credit)}")
    fm.append("---")
    fm.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(fm) + body)
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
