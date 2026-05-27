#!/usr/bin/env python3
"""Update the footer-links block across all HTML files.

Old:  About | Publications | Embassies Monitor | People | Support | Contact
New:  About | Our Work | Advisory | People | Support | Contact
"""
import pathlib
import re

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


def footer_links(prefix, contact_href):
    return (
        '<div class="footer-links">\n'
        f'                    <a href="{prefix}about.html">About</a>\n'
        f'                    <a href="{prefix}our-work/index.html">Our Work</a>\n'
        f'                    <a href="{prefix}advisory.html">Advisory</a>\n'
        f'                    <a href="{prefix}people.html">People</a>\n'
        f'                    <a href="{prefix}support.html">Support</a>\n'
        f'                    <a href="{contact_href}">Contact</a>\n'
        '                </div>'
    )


BLOCK_RE = re.compile(r'<div class="footer-links">.*?</div>', re.DOTALL)


def update_file(path, prefix, contact_href):
    text = path.read_text()
    new = BLOCK_RE.sub(footer_links(prefix, contact_href), text, count=1)
    if new == text:
        return False
    path.write_text(new)
    return True


def main():
    ok, skip = 0, 0
    targets = [(p, "", "index.html#contact") for p in ROOT_PAGES if p.exists()]
    for p in nested_files():
        targets.append((p, "../", "../index.html#contact"))
    for path, prefix, contact in targets:
        rel = path.relative_to(ROOT)
        if update_file(path, prefix, contact):
            ok += 1
            print(f"  ok   {rel}")
        else:
            skip += 1
            print(f"  SKIP {rel}")
    print(f"\n{ok} updated, {skip} skipped")


if __name__ == "__main__":
    main()
