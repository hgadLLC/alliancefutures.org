#!/usr/bin/env python3
"""Convert publications/*-red-team.html into content/research/*.md using the
red-team layout. The article body is stored as markdown with HTML fall-through
for memo blocks and crimson callouts."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "publications"
OUT_DIR = ROOT / "content" / "research"

MONTHS = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,"July":7,
          "August":8,"September":9,"October":10,"November":11,"December":12,
          "Jan":1,"Feb":2,"Mar":3,"Apr":4,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Sept":9,
          "Oct":10,"Nov":11,"Dec":12}


def yq(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def yblock(value: str, indent: int = 0) -> str:
    inner = " " * (indent + 2)
    lines = [(inner + ln) if ln else "" for ln in value.split("\n")]
    return "|\n" + "\n".join(lines)


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


def html_passthrough(node: Tag) -> str:
    """Render the node's full HTML (used for memo-block, crimson-callout)."""
    return str(node).strip() + "\n"


def block_md(node: Tag) -> str:
    if node.name == "p":
        return inline_md(node).rstrip() + "\n"
    if node.name in ("h2", "h3", "h4"):
        level = int(node.name[1])
        anchor = node.get("id")
        text = inline_md(node).strip()
        # Use raw HTML rather than the `{#anchor}` markdown extension — Nunjucks
        # (Eleventy's default markdown template engine) treats `{#` as a comment.
        if anchor:
            return f'<h{level} id="{anchor}">{text}</h{level}>\n'
        return ("#" * level) + " " + text + "\n"
    if node.name in ("ul", "ol"):
        bullet_fn = (lambda i: "- ") if node.name == "ul" else (lambda i: f"{i+1}. ")
        lines = []
        for idx, li in enumerate(node.find_all("li", recursive=False)):
            inner_paras = li.find_all("p", recursive=False)
            if inner_paras:
                first = inner_paras[0]
                first_text = inline_md(first).strip()
                line = bullet_fn(idx) + first_text
                lines.append(line)
                for p in inner_paras[1:]:
                    lines.append("    " + inline_md(p).strip())
            else:
                lines.append(bullet_fn(idx) + inline_md(li).strip())
        return "\n".join(lines) + "\n"
    if node.name == "hr":
        cls = node.get("class") or []
        if "section-divider" in cls:
            return '<hr class="section-divider">\n'
        return "---\n"
    if node.name == "div":
        cls = node.get("class") or []
        if "memo-block" in cls or "memo" in cls or "crimson-callout" in cls:
            return html_passthrough(node)
        return ""
    if node.name == "figure":
        img = node.find("img")
        src = img.get("src", "") if img else ""
        if src.startswith("images/"):
            src = "/publications/" + src
        alt = img.get("alt", "") if img else ""
        return f"![{alt}]({src})\n"
    return ""


def parse_date(s: str) -> str:
    s = s.strip()
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})$", s)
    if m:
        return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    return ""


def parse_byline(text: str) -> tuple[list[str], str]:
    text = text.replace("&middot;", "·").replace("·", "·")
    text = re.sub(r"^\s*By\s+", "", text).strip()
    parts = [p.strip() for p in re.split(r"\s*·\s*", text) if p.strip()]
    iso_date = ""
    authors: list[str] = []
    for p in parts:
        d = parse_date(p)
        if d:
            iso_date = d
        else:
            authors.append(p)
    return authors, iso_date


def parse_toc(article: Tag) -> list[dict]:
    """Build TOC frontmatter by walking the article's h2 elements (and any h3
    elements between an `id=scenarios` h2 and the next h2)."""
    toc = []
    h2s = article.find_all("h2")
    for h2 in h2s:
        item = {"id": h2.get("id", ""), "title": inline_md(h2).strip()}
        if item["id"] == "scenarios":
            subs = []
            n = h2.next_sibling
            while n is not None:
                if isinstance(n, Tag):
                    if n.name == "h2":
                        break
                    if n.name == "div" and "memo-block" in (n.get("class") or []):
                        sub_id = n.get("id", "")
                        sub_h4 = n.find("h4")
                        sub_title = ""
                        meta = n.select_one(".memo-meta")
                        if meta:
                            subj_p = next((p for p in meta.find_all("p") if p.get_text(strip=True).startswith("SUBJ:")), None)
                            if subj_p:
                                t = subj_p.get_text(strip=True)
                                m = re.match(r"SUBJ:\s*([A-Z][A-Z\s]+?)\s+", t)
                                if m:
                                    sub_title = m.group(1).strip().title()
                        if not sub_title and sub_id:
                            sub_title = sub_id.replace("-", " ").title()
                        subs.append({"id": sub_id, "title": sub_title})
                n = n.next_sibling
            if subs:
                item["sub"] = subs
        toc.append(item)
    return toc


def parse_report(html_path: Path) -> tuple[str, str]:
    soup = BeautifulSoup(html_path.read_text(), "html.parser")

    page_hero = soup.select_one("section.page-hero")
    title_h1 = page_hero.find("h1")
    title_html = "".join(str(c) for c in title_h1.children).strip()
    subtitle_p = page_hero.find("p")
    subtitle = inline_md(subtitle_p).strip() if subtitle_p else ""
    byline_div = page_hero.select_one(".report-byline")
    authors, date_iso = parse_byline(byline_div.get_text(" ", strip=True)) if byline_div else ([], "")

    article = soup.select_one("article.report-content")
    if not article:
        raise ValueError(f"No article in {html_path}")

    pdf_a = article.select_one("a.generate-pdf-btn")
    pdf = pdf_a.get("href", "") if pdf_a else None
    if pdf and not pdf.startswith("/") and not pdf.startswith("http"):
        pdf = "/publications/" + pdf

    pub_header = article.select_one(".publication-header .publication-title")
    publication_title = pub_header.get_text(strip=True) if pub_header else ""

    toc = parse_toc(article)

    body_parts: list[str] = []
    for n in article.children:
        if not isinstance(n, Tag):
            continue
        cls = n.get("class") or []
        if n.name == "div" and "publication-header" in cls:
            continue
        if n.name == "a" and "generate-pdf-btn" in cls:
            continue
        if n.name == "div" and "report-endmatter" in cls:
            break
        if n.name == "aside" and "support-cta" in cls:
            continue
        if n.name == "nav" and "pub-nav" in cls:
            continue
        md = block_md(n)
        if md.strip():
            body_parts.append(md)

    body = "\n".join(body_parts).rstrip() + "\n"

    endmatter = article.select_one(".report-endmatter")
    about = disclaimer = acknowledgements = ""
    if endmatter:
        cur_label = None
        for child in endmatter.children:
            if not isinstance(child, Tag):
                continue
            if child.name == "h3":
                cur_label = child.get_text(strip=True).lower()
                continue
            if child.name == "p":
                cls = child.get("class") or []
                if "copyright" in cls:
                    continue
                txt = inline_md(child).strip()
                if cur_label and "about" in cur_label:
                    about = (about + "\n\n" + txt) if about else txt
                elif cur_label and "disclaimer" in cur_label:
                    disclaimer = (disclaimer + "\n\n" + txt) if disclaimer else txt
                elif cur_label and "acknowledg" in cur_label:
                    acknowledgements = (acknowledgements + "\n\n" + txt) if acknowledgements else txt

    desc_meta = soup.find("meta", attrs={"name": "description"})
    description = desc_meta.get("content", "") if desc_meta else ""

    slug = html_path.stem

    fm = ["---", "layout: layouts/red-team.njk", f"slug: {slug}",
          f"date: {date_iso}" if date_iso else "date: 2026-01-01",
          f"title: {yq(title_html)}"]
    if subtitle:
        fm.append(f"subtitle: {yq(subtitle)}")
    if publication_title:
        fm.append(f"publication_title: {yq(publication_title)}")
    if description:
        fm.append(f"description: {yq(description)}")
    if pdf:
        fm.append(f"pdf: {pdf}")
    if authors:
        fm.append("authors:")
        for a in authors:
            fm.append(f"  - {yq(a)}")
    if toc:
        fm.append("toc:")
        for item in toc:
            fm.append(f"  - id: {item['id']}")
            fm.append(f"    title: {yq(item['title'])}")
            if item.get("sub"):
                fm.append("    sub:")
                for sub in item["sub"]:
                    fm.append(f"      - id: {sub['id']}")
                    fm.append(f"        title: {yq(sub['title'])}")
    if about:
        fm.append("about: " + yblock(about, indent=0))
    if disclaimer:
        fm.append("disclaimer: " + yblock(disclaimer, indent=0))
    if acknowledgements:
        fm.append("acknowledgements: " + yblock(acknowledgements, indent=0))
    fm.append("categories: [research, red-team]")
    fm.append("featured: true")
    fm.append("---")
    fm.append("")
    return slug, "\n".join(fm) + body


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(SRC_DIR.glob("*-red-team.html"))
    for f in files:
        slug, md = parse_report(f)
        out = OUT_DIR / f"{slug}.md"
        out.write_text(md)
        print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
