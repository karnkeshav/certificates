#!/usr/bin/env python3
"""Generate a Certificate of Achievement PDF from templates/certificate.html + config.json."""

import argparse
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Simple line-icon set (24x24 viewBox) cycled across the achievement highlight items.
HIGHLIGHT_ICONS = [
    # chat / prompt
    '<svg viewBox="0 0 24 24" fill="none" stroke="#16213e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 5h16a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9l-4 3v-3H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/></svg>',
    # sparkle / strategic
    '<svg viewBox="0 0 24 24" fill="none" stroke="#16213e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>'
    '<circle cx="12" cy="12" r="3"/></svg>',
    # target / integrity
    '<svg viewBox="0 0 24 24" fill="none" stroke="#16213e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/></svg>',
    # book / knowledge
    '<svg viewBox="0 0 24 24" fill="none" stroke="#16213e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 5c2-1 5-1 8 1 3-2 6-2 8-1v13c-2-1-5-1-8 1-3-2-6-2-8-1V5z"/></svg>',
    # person / conceptual
    '<svg viewBox="0 0 24 24" fill="none" stroke="#16213e" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></svg>',
]

SEAL_RING_RADIUS = 39
SEAL_RING_ARC_DEGREES = 250


def ordinal_date(d: date) -> str:
    day = d.day
    if 11 <= day % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {d.strftime('%B %Y')}"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "recipient"


def make_cert_id(prefix: str, track_letter: str, on_date: date) -> str:
    sequence = random.randint(1, 999)
    return f"{prefix}-{track_letter}-{on_date.strftime('%Y%m%d')}-{sequence:03d}"


def parse_highlights(raw: str) -> list:
    """Parse 'Title | Description; Title | Description; ...' into a list of dicts.

    GitHub Actions workflow_dispatch string inputs are single-line, so highlight
    items are separated by ';' and each item's title/description by '|'.
    """
    highlights = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        title, _, desc = chunk.partition("|")
        highlights.append({"title": title.strip(), "desc": desc.strip()})
    return highlights


def build_highlights_html(highlights: list) -> str:
    items = []
    for i, item in enumerate(highlights):
        icon = HIGHLIGHT_ICONS[i % len(HIGHLIGHT_ICONS)]
        items.append(
            '<li class="highlight-item">'
            f'<div class="highlight-icon">{icon}</div>'
            '<div>'
            f'<div class="highlight-title">{item["title"]}</div>'
            f'<div class="highlight-desc">{item["desc"]}</div>'
            '</div>'
            '</li>'
        )
    return "\n".join(items)


def build_seal_ring_html(text: str) -> str:
    n = len(text)
    if n == 0:
        return ""
    if n == 1:
        angles = [0.0]
    else:
        step = SEAL_RING_ARC_DEGREES / (n - 1)
        start = -SEAL_RING_ARC_DEGREES / 2
        angles = [start + step * i for i in range(n)]
    spans = []
    for ch, angle in zip(text, angles):
        display_ch = "&nbsp;" if ch == " " else ch
        spans.append(
            f'<span class="seal-char" style="transform: rotate({angle:.2f}deg) '
            f'translate(-50%, -{SEAL_RING_RADIUS}px);">{display_ch}</span>'
        )
    return "\n".join(spans)


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fill_template(template: str, values: dict) -> str:
    for key, val in values.items():
        template = template.replace("{{" + key + "}}", val)
    return template


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate a Certificate of Achievement PDF.")
    parser.add_argument("--name", required=True, help="Recipient's full name")
    parser.add_argument("--date", default=None, help='Completion date, e.g. "3rd July 2026" (default: today)')
    parser.add_argument("--cert-id", default=None, help="Certificate ID (default: auto-generated)")
    parser.add_argument("--track-letter", default=None, help="Track letter, e.g. A (default: from config)")
    parser.add_argument("--track-full", default=None, help="Track full name (default: from config)")
    parser.add_argument("--duration", default=None, help='Program duration, e.g. "5 days" (default: from config)')
    parser.add_argument("--time-commitment", default=None, help='Time commitment, e.g. "1 hour per day" (default: from config)')
    parser.add_argument("--mode", default=None, help='Delivery mode, e.g. "Live and hands-on practice" (default: from config)')
    parser.add_argument("--highlights-intro", default=None, help="Achievement highlights intro paragraph (default: from config)")
    parser.add_argument(
        "--highlights",
        default=None,
        help="Achievement highlights as 'Title | Description; Title | Description; ...' "
        "(default: from config)",
    )
    parser.add_argument("--config", default=str(ROOT / "templates" / "config.json"), help="Path to config.json")
    parser.add_argument("--template", default=str(ROOT / "templates" / "certificate.html"), help="Path to certificate.html")
    parser.add_argument("--output", default=None, help="Output PDF path (default: output/<slug>-certificate.pdf)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    config_path = Path(args.config)
    template_path = Path(args.template)
    config = load_config(config_path)
    template = template_path.read_text(encoding="utf-8")

    today = date.today()
    completion_date = args.date or ordinal_date(today)
    track_letter = args.track_letter or config["track_letter"]
    track_full = args.track_full or config["track_full"]
    duration = args.duration or config["duration"]
    time_commitment = args.time_commitment or config["time_commitment"]
    mode = args.mode or config["mode"]
    highlights_intro = args.highlights_intro or config["highlights_intro"]
    highlights = parse_highlights(args.highlights) if args.highlights else config["highlights"]
    cert_id = args.cert_id or make_cert_id(config["cert_id_prefix"], track_letter, today)

    values = {
        "RECIPIENT_NAME": args.name,
        "COMPLETION_DATE": completion_date,
        "CERT_ID": cert_id,
        "TRACK_LETTER": track_letter,
        "TRACK_FULL": track_full,
        "PROGRAM_NAME": config["program_name"],
        "BRAND_PREFIX": config["brand_prefix"],
        "BRAND_ACCENT": config["brand_accent"],
        "BRAND_SUFFIX": config["brand_suffix"],
        "TAGLINE": config["tagline"],
        "FOOTER_TAGLINE": config["footer_tagline"],
        "DURATION": duration,
        "TIME_COMMITMENT": time_commitment,
        "MODE": mode,
        "HIGHLIGHTS_INTRO": highlights_intro,
        "HIGHLIGHTS_HTML": build_highlights_html(highlights),
        "CLOSING_STATEMENT": config["closing_statement"],
        "SIGNATORY_NAME": config["signatory_name"],
        "SIGNATORY_ROLE": config["signatory_role"],
        "SIGNATORY_SIGNATURE_IMG": config["signatory_signature_image"],
        "SEAL_INITIALS": config["seal_initials"],
        "SEAL_SUBTEXT": config["seal_subtext"],
        "SEAL_RING_CHARS": build_seal_ring_html(config["seal_ring_text"]),
        "WEBSITE": config["website"],
        "SOCIAL_HANDLE": config["social_handle"],
    }

    html = fill_template(template, values)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = ROOT / "output" / f"{slugify(args.name)}-certificate.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from weasyprint import HTML

    HTML(string=html, base_url=str(template_path.parent)).write_pdf(str(output_path))
    print(f"Certificate written to {output_path}")
    print(f"Certificate ID: {cert_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
