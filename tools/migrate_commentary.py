#!/usr/bin/env python3
"""Convert our-work/commentary/*.html into Eleventy markdown files at
content/commentary/*.md using the commentary layout."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "our-work" / "commentary"
OUT_DIR = ROOT / "content" / "commentary"


MONTHS = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,
          "July":7,"August":8,"September":9,"October":10,"November":11,"December":12,
          "Jan":1,"Feb":2,"Mar":3,"Apr":4,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Sept":9,
          "Oct":10,"Nov":11,"Dec":12}


def inline_md(node) -> str:
    out: list[str] = []
    children = node.children if isinstance(node, Tag) else [node]
    for child in children:
        if isinstance(child, NavigableString):
            out.append(str(child))
        elif isinstance(child, Tag):
            if child.name == "a":
                out.append(f"[{inline_md(child)}]({child.get('href','')})")
            elif child.name in ("strong", "b"):
                out.append(f"**{inline_md(child)}**")
            elif child.name in ("em", "i"):
                out.append(f"*{inline_md(child)}*")
            elif child.name == "br":
                out.append("  \n")
            else:
                out.append(inline_md(child))
    return "".join(out)


def block_md(node: Tag) -> str:
    if node.name == "p":
        cls = node.get("class") or []
        if "lede" in cls:
            return ""
        text = inline_md(node).rstrip()
        if "signoff" in cls:
            return f'<p class="signoff">{text}</p>\n'
        if "one-line" in cls:
            return f'<p class="one-line">{text}</p>\n'
        return text + "\n"
    if node.name == "blockquote":
        text = inline_md(node).strip()
        text = re.sub(r"\s+", " ", text)
        return f"> {text}\n"
    if node.name == "div":
        cls = node.get("class") or []
        if "question-list" in cls:
            parts = ['<div class="question-list">']
            for p in node.find_all("p", recursive=False):
                parts.append(f'  <p>{inline_md(p).strip()}</p>')
            parts.append("</div>")
            return "\n".join(parts) + "\n"
        return ""
    if node.name in ("h2", "h3", "h4"):
        return ("#" * int(node.name[1])) + " " + inline_md(node).strip() + "\n"
    if node.name in ("ul", "ol"):
        bullet = "- " if node.name == "ul" else "1. "
        lines = []
        for li in node.find_all("li", recursive=False):
            lines.append(bullet + inline_md(li).strip())
        return "\n".join(lines) + "\n"
    if node.name == "figure":
        img = node.find("img")
        src = img.get("src", "") if img else ""
        if src.startswith("images/"):
            src = "/our-work/commentary/" + src
        alt = img.get("alt", "") if img else ""
        return f"![{alt}]({src})\n"
    return ""


def parse_date(s: str) -> str:
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})$", s.strip())
    if not m:
        raise ValueError(f"Bad date: {s!r}")
    return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def yaml_quote(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def yaml_block(value: str, indent: int = 0) -> str:
    inner = " " * (indent + 2)
    lines = [(inner + ln) if ln else "" for ln in value.split("\n")]
    return "|\n" + "\n".join(lines)


def parse_commentary(html_path: Path) -> tuple[str, str]:
    soup = BeautifulSoup(html_path.read_text(), "html.parser")

    hero = soup.select_one("section.commentary-hero")
    eyebrow = hero.select_one(".commentary-eyebrow")
    series = eyebrow.get_text(strip=True) if eyebrow else "Commentary"
    title = hero.select_one(".commentary-title").get_text(strip=True)
    byline_div = hero.select_one(".commentary-byline")
    btxt = byline_div.get_text(" ", strip=True)
    bm = re.match(r"By\s+(.+?)\s+·\s+(.+?)\s+·\s+(.+)$", btxt.replace("&middot;", "·").replace("·", "·"))
    author = author_title = date_str = ""
    if bm:
        author, author_title, date_str = bm.group(1), bm.group(2), bm.group(3)
    else:
        bm2 = re.match(r"By\s+(.+?)\s+·\s+(.+)$", btxt)
        if bm2:
            author = bm2.group(1)
            date_str = bm2.group(2)

    iso_date = parse_date(date_str) if date_str else ""

    pdf_a = hero.select_one("a.commentary-download")
    pdf = pdf_a.get("href", "") if pdf_a else None
    if pdf and not pdf.startswith("/") and not pdf.startswith("http"):
        pdf = "/our-work/commentary/" + pdf

    hero_img_el = hero.select_one(".commentary-hero-image img")
    hero_image = hero_img_el.get("src", "") if hero_img_el else ""
    if hero_image.startswith("images/"):
        hero_image = "/our-work/commentary/" + hero_image

    article = soup.select_one("article.commentary-prose")
    lede_p = article.select_one("p.lede") if article else None
    lede = inline_md(lede_p).strip() if lede_p else ""

    body_parts: list[str] = []
    if article:
        for n in article.children:
            if not isinstance(n, Tag):
                continue
            md = block_md(n)
            if md.strip():
                body_parts.append(md)
    body = "\n".join(body_parts).rstrip() + "\n"

    author_block = soup.select_one("aside.author-block")
    author_image = ""
    author_bio = ""
    author_bio_link = ""
    if author_block:
        img = author_block.find("img")
        if img:
            src = img.get("src", "")
            if src.startswith("../../"):
                src = "/" + src[len("../../"):]
            author_image = src
        bio_paras = author_block.find_all("p")
        if len(bio_paras) >= 2:
            bio_p = bio_paras[1]
            for a in bio_p.find_all("a"):
                if "/team/" in a.get("href", "") or "Read full bio" in a.get_text():
                    href = a.get("href", "")
                    if href.startswith("../../"):
                        href = "/" + href[len("../../"):]
                    author_bio_link = href
                    a.extract()
                    break
            author_bio = inline_md(bio_p).strip()

    nav_el = soup.select_one("nav.commentary-nav")
    prev_slug = next_slug = None
    if nav_el:
        for a in nav_el.find_all("a"):
            href = a.get("href", "")
            if href.endswith(".html") and "/commentary" not in href:
                t = a.get_text(strip=True)
                slug = href.replace(".html", "")
                if "Previous" in t:
                    prev_slug = slug
                elif "Next" in t:
                    next_slug = slug

    slug = html_path.stem

    desc_meta = soup.find("meta", attrs={"name": "description"})
    description = desc_meta.get("content", "") if desc_meta else ""

    fm = [
        "---",
        "layout: layouts/commentary.njk",
        f"slug: {slug}",
        f"date: {iso_date}",
        f"title: {yaml_quote(title)}",
        f"series: {yaml_quote(series)}",
        f"author: {yaml_quote(author)}",
    ]
    if author_title:
        fm.append(f"author_title: {yaml_quote(author_title)}")
    if description:
        fm.append(f"description: {yaml_quote(description)}")
    if pdf:
        fm.append(f"pdf: {pdf}")
    if hero_image:
        fm.append(f"hero_image: {hero_image}")
    if lede:
        fm.append("lede: " + yaml_block(lede, indent=0))
    if author_image:
        fm.append(f"author_image: {author_image}")
    if author_bio:
        fm.append("author_bio: " + yaml_block(author_bio, indent=0))
    if author_bio_link:
        fm.append(f"author_bio_link: {author_bio_link}")
    if prev_slug:
        fm.append(f"prev_slug: {prev_slug}")
    if next_slug:
        fm.append(f"next_slug: {next_slug}")
    fm.append("featured: false")
    fm.append("---")
    fm.append("")
    return slug, "\n".join(fm) + body


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC_DIR.glob("*.html"))
    n = 0
    for f in files:
        slug, md = parse_commentary(f)
        out = OUT_DIR / f"{slug}.md"
        out.write_text(md)
        print(f"wrote {out.relative_to(ROOT)}")
        n += 1
    print(f"\nWrote {n} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
