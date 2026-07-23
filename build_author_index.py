#!/usr/bin/env python3
"""Build an alphabetical author index from an abstract JSON file."""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT / "dist"


@dataclass
class AuthorEntry:
    display_name: str
    sort_key: tuple[str, str, str]
    talk_ids: list[str] = field(default_factory=list)


def clean_name_part(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def author_name(author: dict[str, Any]) -> tuple[str, tuple[str, str, str], str]:
    last = clean_name_part(author.get("last_name_en"))
    first = clean_name_part(author.get("first_name_en"))
    middle = clean_name_part(author.get("middle_name"))
    given = " ".join(part for part in (first, middle) if part)

    if last and given:
        display = f"{last}, {given}"
    else:
        display = last or given

    key = (normalized(last), normalized(given), normalized(display))
    # Use the structured name as the identity. NFKC/casefold also merges harmless
    # differences in width and capitalization between submissions.
    identity = "\0".join((normalized(last), normalized(first), normalized(middle)))
    return display, key, identity


def parse_order(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def load_index(path: Path) -> list[AuthorEntry]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")

    records = sorted(
        enumerate(data),
        key=lambda item: (
            parse_order(item[1].get("掲載順序"), item[0] + 1),
            str(item[1].get("talk_id") or item[1].get("講演番号") or ""),
        ),
    )
    entries: OrderedDict[str, AuthorEntry] = OrderedDict()

    for _, record in records:
        talk_id = clean_name_part(record.get("talk_id") or record.get("講演番号"))
        if not talk_id:
            continue
        authors = record.get("coauthors") or []
        if not isinstance(authors, list):
            raise ValueError(f"{talk_id}: coauthors must be an array")

        for author in authors:
            if not isinstance(author, dict):
                raise ValueError(f"{talk_id}: each coauthor must be an object")
            display, sort_key, identity = author_name(author)
            if not display:
                continue
            entry = entries.setdefault(identity, AuthorEntry(display, sort_key))
            if talk_id not in entry.talk_ids:
                entry.talk_ids.append(talk_id)

    return sorted(entries.values(), key=lambda entry: entry.sort_key)


def render_html(entries: list[AuthorEntry]) -> str:
    rows = "\n".join(
        "      <tr>"
        f'<td class="author">{html.escape(entry.display_name)}</td>'
        f'<td class="talks">{html.escape(", ".join(entry.talk_ids))}</td>'
        "</tr>"
        for entry in entries
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Author Index</title>
  <link rel="stylesheet" href="author_index.css">
</head>
<body>
  <main>
    <table>
      <tbody>
{rows}
      </tbody>
    </table>
  </main>
</body>
</html>
"""


CSS = """\
@page {
  size: A5 portrait;
  margin: 15mm 15mm 10mm;

  @top-center {
    content: "Author Index";
    width: 100%;
    border-bottom: 0.25pt solid #000;
    font-family: "Times New Roman", "Nimbus Roman", serif;
    font-size: 9pt;
    line-height: 1.2;
    vertical-align: bottom;
  }
}

html {
  font-family: "Times New Roman", "Nimbus Roman", serif;
  font-size: 8pt;
  line-height: 1.2;
}

body { margin: 0; color: #111; }
table { width: 100%; border-collapse: collapse; }
tr { break-inside: avoid; }
td { padding: 1.27mm 0 0; vertical-align: top; }
.author { width: 28.25%; padding-right: 2mm; }
.talks { width: 71.75%; }
"""


def write_outputs(entries: list[AuthorEntry], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "author_index.html").write_text(render_html(entries), encoding="utf-8")
    (output_dir / "author_index.css").write_text(CSS, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    entries = load_index(args.input)
    write_outputs(entries, args.output_dir)
    print(f"authors: {len(entries)}")
    print(f"html: {args.output_dir / 'author_index.html'}")
    print(f"css: {args.output_dir / 'author_index.css'}")


if __name__ == "__main__":
    main()
