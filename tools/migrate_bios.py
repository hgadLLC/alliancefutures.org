#!/usr/bin/env python3
"""Import the PEOPLE dict from team/_build_bios.py and emit one markdown file
per person under content/people/. Recent Work is rendered by the bio layout
at build time using shared data files."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "content" / "people"


def load_people():
    spec = importlib.util.spec_from_file_location("_build_bios", ROOT / "team" / "_build_bios.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PEOPLE


def yq(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def yblock(value: str, indent: int = 0) -> str:
    inner = " " * (indent + 2)
    lines = [(inner + ln) if ln else "" for ln in value.split("\n")]
    return "|\n" + "\n".join(lines)


def emit_person(p: dict) -> str:
    fm = ["---", "layout: layouts/bio.njk", f"slug: {p['slug']}",
          f"name: {yq(p['name'])}",
          f"role: {yq(p['title'])}",
          f"photo: {p['photo']}"]
    if p.get("email"):
        fm.append(f"email: {p['email']}")
    if p.get("linkedin"):
        fm.append(f"linkedin: {p['linkedin']}")
    if p.get("hero_lede"):
        fm.append("hero_lede: " + yblock(p["hero_lede"], indent=0))
    if p.get("lede_p"):
        fm.append("lede_p: " + yblock(p["lede_p"], indent=0))
    if p.get("focus"):
        fm.append("focus:")
        for f in p["focus"]:
            fm.append(f"  - {yq(f)}")
    if p.get("affiliations"):
        fm.append("affiliations:")
        for a in p["affiliations"]:
            fm.append(f"  - {yq(a)}")
    if p.get("education"):
        fm.append("education:")
        for e in p["education"]:
            fm.append(f"  - {yq(e)}")
    if p.get("prev"):
        fm.append(f"prev_slug: {p['prev'][0]}")
        fm.append(f"prev_name: {yq(p['prev'][1])}")
    if p.get("next"):
        fm.append(f"next_slug: {p['next'][0]}")
        fm.append(f"next_name: {yq(p['next'][1])}")
    fm.append("---")
    fm.append("")

    body_parts: list[str] = []
    for label, paras in p.get("sections", []):
        body_parts.append(f"## {label}")
        body_parts.append("")
        for para in paras:
            body_parts.append(para)
            body_parts.append("")
    return "\n".join(fm) + "\n".join(body_parts).rstrip() + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    people = load_people()
    for p in people:
        out = OUT_DIR / f"{p['slug']}.md"
        out.write_text(emit_person(p))
        print(f"wrote {out.relative_to(ROOT)}")
    print(f"\nWrote {len(people)} bio files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
