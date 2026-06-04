"""
parse_bib.py
Converts a .bib file into a machine-readable JSON file containing only:
  - citation key
  - title
  - doi

Usage:
    python parse_bib.py input.bib output.json
    python parse_bib.py input.bib              # writes to input.json by default
"""

import re
import json
import sys
from pathlib import Path


def parse_bib_file(bib_text: str) -> list[dict]:
    """Parse raw .bib content and return a list of entry dicts."""
    entries = []

    # Match each @type{key, ...} block
    entry_pattern = re.compile(
        r"@\w+\{([^,]+),(.+?)(?=\n@|\Z)", re.DOTALL
    )

    for match in entry_pattern.finditer(bib_text):
        citation_key = match.group(1).strip()
        body = match.group(2)

        title = extract_field(body, "title")
        doi = extract_field(body, "doi")
        url = extract_field(body, "url")

        entries.append({
            "citation_key": citation_key,
            "title": title,
            "doi": doi if doi else url,
        })

    return entries


def extract_field(body: str, field: str) -> str | None:
    """Extract the value of a named field from a BibTeX entry body.

    Handles values wrapped in braces (possibly nested) or double-quotes.
    """
    # Find the start of the field value after 'fieldname ='
    pattern = re.compile(
        rf"^\s*{field}\s*=\s*",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(body)
    if not match:
        return None

    rest = body[match.end():]

    if rest.startswith("{"):
        # Walk the string tracking brace depth to find the matching closing brace
        depth = 0
        chars = []
        for ch in rest:
            if ch == "{":
                depth += 1
                if depth > 1:          # skip the outermost braces
                    chars.append(ch)
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
                chars.append(ch)
            else:
                chars.append(ch)
        value = "".join(chars)
    elif rest.startswith('"'):
        # Double-quoted value — grab everything up to the closing quote
        end = rest.find('"', 1)
        value = rest[1:end] if end != -1 else ""
    else:
        return None

    # Collapse internal whitespace / newlines and strip nested case-protection braces
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace("{", "").replace("}", "")
    return value if value else None


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_bib.py <input.bib> [output.json]")
        sys.exit(1)

    bib_path = Path(sys.argv[1])
    if not bib_path.exists():
        print(f"Error: file not found — {bib_path}")
        sys.exit(1)

    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else bib_path.with_suffix(".json")

    bib_text = bib_path.read_text(encoding="utf-8")
    entries = parse_bib_file(bib_text)

    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Parsed {len(entries)} entries → {out_path}")


if __name__ == "__main__":
    main()
