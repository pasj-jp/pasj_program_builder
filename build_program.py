#!/usr/bin/env python3
"""Build a printable program booklet HTML from an abstract JSON file.

The generated HTML is intended to be typeset to PDF by Vivliostyle.
It deliberately uses only the Python standard library so that the data
conversion step is easy to run on a fresh server.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT / "dist"


ALLOWED_INLINE_TAGS = {"sup", "sub", "i", "em", "b", "strong", "br"}


@dataclass
class Presentation:
    order: int
    code: str
    session: str
    category: str
    date: str
    time: str
    room: str
    presentation_type: str
    category_1: str
    title_ja: str
    title_en: str
    presenter_ja: str
    presenter_en: str
    presenter_affiliation_en: str
    authors_en_html: str


@dataclass
class ProgramBlock:
    date: str
    room: str
    session: str
    start_time: str
    end_time: str
    presentations: list[Presentation]
    chair: str = ""
    heading: str = ""


def parse_order(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def strip_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"</?(?:sup|sub|i|em|b|strong)[^>]*>", "", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def safe_inline_html(value: str) -> str:
    """Escape arbitrary HTML but preserve a small set of inline tags.

    Abstract JSON files contain preformatted author strings with <sup> markers.
    We keep those while avoiding accidental layout-breaking markup.
    """

    placeholders: list[str] = []

    def keep(match: re.Match[str]) -> str:
        token = f"@@HTML{len(placeholders)}@@"
        tag = match.group(0)
        name = re.sub(r"^</?\s*([a-zA-Z0-9]+).*$", r"\1", tag).lower()
        if name in ALLOWED_INLINE_TAGS:
            # Drop attributes except for the tag name itself.
            closing = "/" if tag.startswith("</") else ""
            if name == "br":
                normalized = "<br>"
            else:
                normalized = f"<{closing}{name}>"
            placeholders.append(normalized)
            return token
        return tag

    protected = re.sub(r"</?\s*[a-zA-Z0-9]+(?:\s+[^>]*)?/?>", keep, value or "")
    escaped = html.escape(protected, quote=False)
    for i, tag in enumerate(placeholders):
        escaped = escaped.replace(f"@@HTML{i}@@", tag)
    return escaped


def format_date_with_weekdays(date_text: str, year: int | None) -> str:
    if year is None:
        return date_text

    match = re.fullmatch(r"(\d+)月(\d+)日(?:・(\d+)日)?", date_text)
    if not match:
        return date_text

    month = int(match.group(1))
    days = [int(match.group(2))]
    if match.group(3):
        days.append(int(match.group(3)))

    weekdays = "月火水木金土日"
    try:
        formatted_days = [
            f"{day}日（{weekdays[date(year, month, day).weekday()]}）"
            for day in days
        ]
    except ValueError:
        return date_text

    return f"{month}月" + "・".join(formatted_days)


def split_time_range(value: str) -> tuple[str, str]:
    if not value or "-" not in value:
        return value or "", value or ""
    start, end = value.split("-", 1)
    return start.strip(), end.strip()


def full_name_ja(record: dict[str, Any]) -> str:
    return " ".join(part for part in [record.get("last_name"), record.get("first_name")] if part).strip()


def full_name_en(record: dict[str, Any]) -> str:
    parts = [record.get("first_name_en"), record.get("middle_name"), record.get("last_name_en")]
    return " ".join(part for part in parts if part).strip()


def presenter_from_authors_en(authors_en_html: str) -> tuple[str, str]:
    """Return presenter's English name and affiliation from the author HTML.

    The source has strings like:
      ○Name<sup>1</sup>, Coauthor<sup>2</sup>（<sup>1</sup>Aff1, <sup>2</sup>Aff2）
    The legacy Word template used only the presenter, not the full author list.
    """

    if not authors_en_html:
        return "", ""

    text = authors_en_html.strip()
    text = text.lstrip("○").strip()

    # Split "authors（affiliations）" while tolerating full-width parentheses.
    authors_part = text
    affiliation_part = ""
    m = re.search(r"[（(](.+)[）)]\s*$", text)
    if m:
        authors_part = text[: m.start()].strip()
        affiliation_part = m.group(1).strip()

    if re.search(r"<sup\b", authors_part, flags=re.I):
        first_match = re.match(r"^(.*?</sup>)", authors_part, flags=re.I)
        first_author = first_match.group(1).strip() if first_match else authors_part.strip()
    else:
        first_author = re.split(r",\s*", authors_part, maxsplit=1)[0].strip()
    sup_numbers = re.findall(r"<sup>\s*([^<]+?)\s*</sup>", first_author, flags=re.I)
    presenter_name = strip_html(re.sub(r"<sup>.*?</sup>", "", first_author, flags=re.I)).strip()

    affiliation = ""
    if affiliation_part:
        affiliation_map: dict[str, str] = {}
        parts = re.split(r"<sup>\s*([^<]+?)\s*</sup>", affiliation_part, flags=re.I)
        # parts: [prefix, number, text, number, text, ...]
        for i in range(1, len(parts), 2):
            number = strip_html(parts[i]).strip()
            value = strip_html(parts[i + 1] if i + 1 < len(parts) else "").strip(" ,、")
            if number and value:
                affiliation_map[number] = value

        numbers: list[str] = []
        for item in sup_numbers:
            numbers.extend(n.strip() for n in re.split(r"[,、]", strip_html(item)) if n.strip())
        values = [affiliation_map[n] for n in numbers if n in affiliation_map]
        affiliation = ", ".join(values)
        if not affiliation:
            affiliation = strip_html(affiliation_part).strip()

    return presenter_name, affiliation


def to_presentation(record: dict[str, Any], index: int) -> Presentation:
    authors_en = (
        record.get("author_text_en_html")
        or record.get("著者情報（英語）")
        or ""
    )
    presenter_from_authors, affiliation_from_authors = presenter_from_authors_en(authors_en)
    presenter_en = presenter_from_authors or full_name_en(record)
    affiliation_en = affiliation_from_authors

    # The Word template used only the presenter and presenter's affiliation.
    # If JSON lacks those in a clean field, derive a readable fallback.
    if not affiliation_en and authors_en:
        m = re.search(r"（(.+?)）\s*$", strip_html(authors_en))
        affiliation_en = m.group(1) if m else ""
    if not affiliation_en:
        # Keep the affiliation beside the English presenter name English-only.
        # Legacy JSON retains the original Japanese header; newly converted
        # JSON uses the normalized key.
        affiliation_en = str(
            record.get("affiliation_text_en_html")
            or record.get("著者所属情報（英語）")
            or ""
        )

    return Presentation(
        order=parse_order(record.get("掲載順序"), index),
        code=str(record.get("talk_id") or record.get("講演番号") or ""),
        session=str(record.get("session") or ""),
        category=str(record.get("category") or ""),
        date=str(record.get("date") or ""),
        time=str(record.get("time") or ""),
        room=str(record.get("room") or ""),
        presentation_type=str(record.get("確定発表形式2") or record.get("presentation_type") or ""),
        category_1=str(record.get("category_1") or "").strip(),
        title_ja=str(record.get("title_ja") or ""),
        title_en=str(record.get("title_en") or ""),
        presenter_ja=full_name_ja(record),
        presenter_en=presenter_en,
        presenter_affiliation_en=strip_html(affiliation_en),
        authors_en_html=authors_en,
    )


def load_presentations(path: Path) -> list[Presentation]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    presentations = [to_presentation(record, i + 1) for i, record in enumerate(data)]
    return sorted(presentations, key=lambda p: (p.order, p.code))


def load_chair_data(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def block_key(presentation: Presentation) -> tuple[str, str, str]:
    return presentation.date, presentation.room, presentation.session


def make_blocks(presentations: list[Presentation], chair_data: dict[str, Any]) -> list[ProgramBlock]:
    blocks: list[ProgramBlock] = []
    current: list[Presentation] = []
    current_key: tuple[str, str, str] | None = None

    for pres in presentations:
        key = block_key(pres)
        if current and key != current_key:
            blocks.append(make_block(current, chair_data))
            current = []
        current_key = key
        current.append(pres)

    if current:
        blocks.append(make_block(current, chair_data))

    return blocks


def make_block(items: list[Presentation], chair_data: dict[str, Any]) -> ProgramBlock:
    first, last = items[0], items[-1]
    start, _ = split_time_range(first.time)
    _, end = split_time_range(last.time)

    block = ProgramBlock(
        date=first.date,
        room=first.room,
        session=first.session,
        start_time=start,
        end_time=end,
        presentations=items,
    )

    chair_key = f"{block.date}|{block.room}|{block.session}"
    chair_entry = chair_data.get(chair_key, {})
    if isinstance(chair_entry, dict):
        block.chair = str(chair_entry.get("chair") or "")
        block.heading = str(chair_entry.get("heading") or "")
        if chair_entry.get("time"):
            block.start_time, block.end_time = split_time_range(str(chair_entry["time"]))

    return block


def block_title(block: ProgramBlock, year: int | None) -> str:
    formatted_date = format_date_with_weekdays(block.date, year)
    time = f"{block.start_time}-{block.end_time}" if block.start_time and block.end_time else ""
    meta_line = "　".join(
        part for part in [formatted_date, time, block.room] if part
    )
    session_line = block.heading or block.session
    if block.chair:
        session_line += f"　座長：{block.chair}"
    return "\n".join(part for part in [meta_line, session_line] if part)


def render_presentation(pres: Presentation) -> str:
    title_en = ""
    if pres.title_en and pres.title_en.strip() != pres.title_ja.strip():
        title_en = f'<div class="title-en">{safe_inline_html(pres.title_en)}</div>'

    affiliation = html.escape(pres.presenter_affiliation_en)
    presenter_ja = html.escape(pres.presenter_ja)
    presenter_en = html.escape(pres.presenter_en)

    return f"""\
        <tr class="paper-title-row">
          <td class="paper-code" rowspan="2">{html.escape(pres.code)}</td>
          <td class="paper-title">
            <div class="title-ja">{safe_inline_html(pres.title_ja)}</div>
            {title_en}
          </td>
        </tr>
        <tr class="paper-author-row">
          <td class="paper-author">
            <div class="presenter-ja">{presenter_ja}</div>
            <div class="presenter-details">
              <span class="presenter-en">{presenter_en}</span>
              {f'<span class="affiliation">（{affiliation}）</span>' if affiliation else ''}
            </div>
          </td>
        </tr>
"""


def render_sub_session_heading(category: str) -> str:
    return f"""\
        <tr class="sub-session-heading">
          <th colspan="2">{html.escape(category)}</th>
        </tr>
"""


def render_block(block: ProgramBlock, year: int | None) -> str:
    rendered_rows: list[str] = []
    current_category = ""
    for pres in block.presentations:
        if pres.category and pres.category != current_category:
            rendered_rows.append(render_sub_session_heading(pres.category))
        current_category = pres.category
        rendered_rows.append(render_presentation(pres))
    rows = "\n".join(rendered_rows)
    heading = html.escape(block_title(block, year)).replace("\n", "<br>\n")
    return f"""\
    <section class="session-block">
      <div class="session-heading">{heading}</div>
      <table class="program-table">
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
"""


def render_html(blocks: list[ProgramBlock], year: int | None) -> str:
    body = "\n".join(render_block(block, year) for block in blocks)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>PASJ2025 Program</title>
  <link rel="stylesheet" href="program.css">
</head>
<body>
  <main class="book">
{body}
  </main>
</body>
</html>
"""


CSS = """\
@page {
  size: A4;
  margin: 8mm 9mm 12mm;

  @bottom-center {
    content: counter(page);
    font-size: 9pt;
  }
}

html {
  font-family: "Hiragino Sans", "Yu Gothic", "Yu Gothic Medium", "Noto Sans CJK JP", "Noto Sans JP", sans-serif;
  font-size: 12pt;
  line-height: 1.25;
}

body {
  margin: 0;
  color: #111;
}

.book {
  width: 100%;
}

.session-block {
  break-before: page;
  page-break-before: always;
  margin: 0 0 2.2mm;
}

.program-table {
  border-collapse: collapse;
  table-layout: fixed;
}

.session-heading {
  box-sizing: border-box;
  width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  break-inside: avoid;
  break-after: avoid-page;
  page-break-after: avoid;
  background: #666;
  color: #fff;
  text-align: center;
  font-weight: 700;
  font-size: 13pt;
  line-height: 1.25;
  padding: 1.3mm 1mm;
  border-top: 0.35pt solid #777;
  border-bottom: 0.35pt solid #777;
}

.paper-code {
  width: 30mm;
  vertical-align: top;
  text-align: left;
  font-weight: 700;
  padding: 1.0mm 0.6mm 0.2mm 0.5mm;
  white-space: nowrap;
}

.sub-session-heading {
  break-inside: avoid;
  break-after: avoid-page;
  page-break-after: avoid;
}

.sub-session-heading th {
  box-sizing: border-box;
  padding: 0.8mm 1mm;
  background: #ddd;
  color: #111;
  text-align: left;
  font-size: 11pt;
  line-height: 1.25;
}

.paper-title {
  vertical-align: top;
  padding: 1.0mm 0 0.2mm;
}

.paper-author {
  vertical-align: top;
  padding: 0 0 1.0mm;
}

.title-ja {
  font-family: "Hiragino Sans", "Yu Gothic", "Yu Gothic Medium", "Noto Sans CJK JP", "Noto Sans JP", sans-serif;
  font-weight: 700;
}

.title-en,
.presenter-en,
.affiliation {
  font-family: "Times New Roman", "Nimbus Roman", serif;
}

.title-en {
  margin-top: 0.2mm;
}

.paper-title-row,
.paper-author-row {
  break-inside: avoid;
}

.paper-author-row td {
  border-bottom: 0.2pt solid transparent;
}

sup {
  font-size: 65%;
  line-height: 0;
}
"""


def write_outputs(html_text: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "program.html").write_text(html_text, encoding="utf-8")
    (output_dir / "program.css").write_text(CSS, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--year", type=int)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--chair", type=Path)
    args = parser.parse_args()

    presentations = load_presentations(args.input)
    chair_data = load_chair_data(args.chair) if args.chair else {}
    blocks = make_blocks(presentations, chair_data)
    write_outputs(render_html(blocks, args.year), args.output_dir)

    print(f"presentations: {len(presentations)}")
    print(f"blocks: {len(blocks)}")
    print(f"html: {args.output_dir / 'program.html'}")
    print(f"css: {args.output_dir / 'program.css'}")


if __name__ == "__main__":
    main()
