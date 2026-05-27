#!/usr/bin/env python3
"""Strip the 1501 M Street mailing address line from every HTML file's footer,
leaving the contact email link in place.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATTERN = re.compile(
    r'Mailing address: 1501 M St NW, Suite 220, Washington, DC 20005\s*&middot;\s*',
)


def main():
    ok, skip = 0, 0
    for path in ROOT.rglob("*.html"):
        if ".playwright-mcp" in path.parts:
            continue
        text = path.read_text()
        new = PATTERN.sub("", text)
        if new != text:
            path.write_text(new)
            ok += 1
            print(f"  ok   {path.relative_to(ROOT)}")
        else:
            skip += 1
    print(f"\n{ok} updated, {skip} unchanged")


if __name__ == "__main__":
    main()
