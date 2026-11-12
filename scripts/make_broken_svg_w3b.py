# -*- coding: utf-8 -*-
"""Make a deliberately broken copy of a rebuilt figure SVG for the rule-8
gate: every text label is re-placed into a tight pile, which must make the
checker FAIL (text/text overlaps + text/segment crossings) before the real
output is accepted.

Usage:
  node scripts/run_py.mjs scripts/make_broken_svg.py <in.svg> <out.svg>
"""
import re
import sys


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        svg = f.read()
    n = [0]

    def get(attrs, name, default):
        m = re.search(r'\b%s="([^"]*)"' % name, attrs)
        return m.group(1) if m else default

    def pile(m):
        attrs = m.group("attrs")
        i = n[0]
        n[0] += 1
        x = 150 + (i % 3) * 60
        y = 120 + i * 6
        # keep only the font attributes; letter-spacing / text-anchor are
        # dropped so the pile is placed purely by the rewritten x/y.
        return '<text x="%d" y="%d" font-size="%s" font-weight="%s" ' \
               'fill="%s">%s</text>' % (
                   x, y, get(attrs, "font-size", "16"),
                   get(attrs, "font-weight", "normal"),
                   get(attrs, "fill", "#000000"), m.group("content"))

    # tolerant: any attribute order / extra attributes (letter-spacing,
    # text-anchor, ...) must still be re-placed into the pile.
    out = re.sub(r'<text (?P<attrs>[^>]*)>(?P<content>[^<]*)</text>',
                 pile, svg)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote", dst, "with", n[0], "piled labels")


if __name__ == "__main__":
    main()
