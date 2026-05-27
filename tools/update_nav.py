#!/usr/bin/env python3
"""Update the Our Work dropdown + add top-level Advisory link across the site.

New nav (4 categories in the Our Work dropdown):
  About | Our Work v | Advisory | People | Support
  Our Work dropdown: Research / Futures / Commentary / Embassies Monitor

This script edits the desktop `<nav>...</nav>` and the mobile `.mobile-nav`
blocks in every HTML file under root and one level deep. Path prefixes
('' for root pages, '../' for nested) are chosen by the file's depth.

The bio generator (team/_build_bios.py) has its own template; this script
updates it as well, then bios should be regenerated.

Usage:  python3 tools/update_nav.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

ROOT_PAGES = [
    ROOT / "index.html",
    ROOT / "about.html",
    ROOT / "advisory.html",
    ROOT / "people.html",
    ROOT / "support.html",
    ROOT / "privacy.html",
]

NESTED_DIRS = ["publications", "embassy-monitors", "team", "our-work"]


def nested_files():
    out = []
    for d in NESTED_DIRS:
        out.extend(sorted((ROOT / d).glob("*.html")))
    return out


def desktop_nav(prefix):
    return f'''<nav>
            <a href="{prefix}about.html">About</a>
            <div class="nav-dropdown">
                <a href="{prefix}our-work/index.html" class="nav-dropdown-trigger">Our Work <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
                <div class="nav-dropdown-menu">
                    <a href="{prefix}our-work/index.html?category=research">Research</a>
                    <a href="{prefix}our-work/index.html?category=futures">Futures</a>
                    <a href="{prefix}our-work/index.html?category=commentary">Commentary</a>
                    <a href="{prefix}embassy-monitors/index.html">Embassies Monitor</a>
                </div>
            </div>
            <a href="{prefix}advisory.html">Advisory</a>
            <a href="{prefix}people.html">People</a>
            <a href="{prefix}support.html">Support</a>
        </nav>'''


def mobile_nav(prefix):
    return f'''<nav class="mobile-nav">
            <a href="{prefix}about.html">About</a>
            <div class="mobile-nav-group">
                <button class="mobile-nav-group-trigger">Our Work <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
                <div class="mobile-nav-group-items">
                    <a href="{prefix}our-work/index.html?category=research">Research</a>
                    <a href="{prefix}our-work/index.html?category=futures">Futures</a>
                    <a href="{prefix}our-work/index.html?category=commentary">Commentary</a>
                    <a href="{prefix}embassy-monitors/index.html">Embassies Monitor</a>
                </div>
            </div>
            <a href="{prefix}advisory.html">Advisory</a>
            <a href="{prefix}people.html">People</a>
            <a href="{prefix}support.html">Support</a>
        </nav>'''


# Match the desktop nav: starts with `<nav>` (no class), ends with `</nav>`.
# Match the mobile nav: starts with `<nav class="mobile-nav">`, ends with `</nav>`.
DESKTOP_RE = re.compile(r'<nav>\s*<a [^>]*?>About</a>.*?</nav>', re.DOTALL)
MOBILE_RE = re.compile(r'<nav class="mobile-nav">.*?</nav>', re.DOTALL)


def update_file(path, prefix):
    text = path.read_text()
    new = DESKTOP_RE.sub(desktop_nav(prefix), text, count=1)
    if new == text:
        return False, "desktop nav not matched"
    after_mobile = MOBILE_RE.sub(mobile_nav(prefix), new, count=1)
    if after_mobile == new:
        return False, "mobile nav not matched"
    path.write_text(after_mobile)
    return True, "ok"


def main():
    ok, fail = 0, 0
    targets = [(p, "") for p in ROOT_PAGES if p.exists()]
    for p in nested_files():
        targets.append((p, "../"))
    for path, prefix in targets:
        success, why = update_file(path, prefix)
        rel = path.relative_to(ROOT)
        if success:
            ok += 1
            print(f"  ok   {rel}")
        else:
            fail += 1
            print(f"  SKIP {rel}  ({why})")
    print(f"\n{ok} updated, {fail} skipped")


if __name__ == "__main__":
    main()
