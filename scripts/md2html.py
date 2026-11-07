#!/usr/bin/env python3
"""Minimal Markdown -> standalone HTML converter for our own docs.

Only the subset we actually write is supported: ATX headings, pipe tables,
bullet/numbered lists, fenced code blocks, block quotes, horizontal rules,
**bold**, *italic*, `code`, [links](url).

It exists so a doc has ONE source (the .md) and the printable/shareable HTML is
generated, instead of two copies drifting apart.

Usage:
    python scripts/md2html.py docs/team_division.md [--out docs/team_division.html]
"""

import argparse
import html
import os
import re
import sys

CSS = """
@page { size: A4; margin: 16mm 14mm; }
* { box-sizing: border-box; }
body {
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  font-size: 10.5pt; line-height: 1.62; color: #1a1a1a; margin: 0 auto;
  max-width: 980px; padding: 18px 22px 40px; background: #fff;
}
h1 { font-size: 21pt; margin: 0 0 4px; letter-spacing: .5px; }
h1 + p { color: #555; margin-top: 0; }
h2 { font-size: 14pt; margin: 26px 0 8px; padding-bottom: 4px;
     border-bottom: 2px solid #1f4e79; color: #1f4e79; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 18px 0 6px; color: #1f4e79; page-break-after: avoid; }
p { margin: 7px 0; }
hr { border: 0; border-top: 1px solid #dcdcdc; margin: 22px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 14px; font-size: 9.5pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #c9d6e3; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #eef3f8; font-weight: 600; }
tbody tr:nth-child(even) td { background: #fafcfe; }
ul, ol { margin: 6px 0 10px; padding-left: 22px; }
li { margin: 3px 0; }
code { background: #f3f4f6; padding: 1px 4px; border-radius: 3px;
       font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; color: #b5304a; }
pre { background: #f7f8fa; border-left: 3px solid #1f4e79; padding: 9px 12px;
      overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; color: #24292f; padding: 0; font-size: 9.5pt; }
blockquote { margin: 10px 0; padding: 6px 12px; border-left: 3px solid #c9d6e3; color: #555; }
strong { color: #12324f; }
a { color: #1f4e79; }
@media print { body { padding: 0; max-width: none; } h1 { font-size: 19pt; } }
"""


def inline(text):
    """Escape then re-introduce the inline markup we support."""
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return "\x00%d\x00" % (len(stash) - 1)

    text = re.sub(r"`([^`]+)`", lambda m: keep("<code>%s</code>" % html.escape(m.group(1))), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: keep('<a href="%s">%s</a>' % (html.escape(m.group(2)), html.escape(m.group(1)))),
                  text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def convert(md):
    out = []
    lines = md.replace("\r\n", "\n").split("\n")
    i = 0
    in_list = None

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</%s>" % in_list)
            in_list = None

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            close_list()
            fence = line.strip()[3:]
            i += 1
            body = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            out.append('<pre><code class="lang-%s">%s</code></pre>'
                       % (html.escape(fence), html.escape("\n".join(body))))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_list()
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, inline(m.group(2).strip()), level))
            i += 1
            continue

        if re.match(r"^\s*---+\s*$", line):
            close_list()
            out.append("<hr>")
            i += 1
            continue

        # table: header row with a |---| separator underneath
        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$", lines[i + 1]):
            close_list()
            header = split_row(line)
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1
            out.append("<table>")
            out.append("<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in header) + "</tr></thead>")
            out.append("<tbody>")
            for r in rows:
                r = (r + [""] * len(header))[:len(header)]
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</tbody></table>")
            continue

        m = re.match(r"^\s*([-*+])\s+(.*)$", line)
        if m:
            if in_list != "ul":
                close_list()
                out.append("<ul>")
                in_list = "ul"
            out.append("<li>%s</li>" % inline(m.group(2)))
            i += 1
            continue

        m = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        if m:
            if in_list != "ol":
                close_list()
                out.append("<ol>")
                in_list = "ol"
            out.append("<li>%s</li>" % inline(m.group(2)))
            i += 1
            continue

        if line.strip().startswith(">"):
            close_list()
            out.append("<blockquote>%s</blockquote>" % inline(line.strip().lstrip(">").strip()))
            i += 1
            continue

        if not line.strip():
            close_list()
            i += 1
            continue

        close_list()
        out.append("<p>%s</p>" % inline(line.strip()))
        i += 1

    close_list()
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out")
    ap.add_argument("--title")
    args = ap.parse_args()

    with open(args.src, encoding="utf-8") as f:
        md = f.read()
    body = convert(md)
    title = args.title or os.path.splitext(os.path.basename(args.src))[0]
    doc = ("<!doctype html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
           "<title>%s</title>\n<style>%s</style></head>\n<body>\n%s\n</body></html>\n"
           % (html.escape(title), CSS, body))

    out = args.out or (os.path.splitext(args.src)[0] + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote %s (%d bytes)" % (out, len(doc.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
