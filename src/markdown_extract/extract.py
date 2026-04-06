"""Core extraction logic for markdown-extract."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


def extract(
    input_path: Union[str, Path],
    *,
    output_dir: Optional[str] = None,
    format: str = "json",
    quiet: bool = False,
    heading_level: Optional[str] = None,
    sections: Optional[str] = None,
    include_frontmatter: bool = True,
    strip_html: bool = False,
    include_code_blocks: bool = True,
    include_toc: bool = False,
    flatten_lists: bool = False,
    section_separator: Optional[str] = None,
    normalize_links: bool = False,
) -> str:
    """Extract structured data from a Markdown file.

    Args:
        input_path: Path to the Markdown file or directory.
        output_dir: Directory where output files are written.
        format: Output format (json, text, html).
        quiet: Suppress console logging output.
        heading_level: Filter by heading levels (comma-separated).
        sections: Extract only sections matching heading text (comma-separated).
        include_frontmatter: Include YAML/TOML frontmatter in output.
        strip_html: Strip inline HTML tags from Markdown content.
        include_code_blocks: Include fenced code blocks in output.
        include_toc: Add a generated table of contents to the output.
        flatten_lists: Flatten nested lists into a single level.
        section_separator: Separator between sections in text output.
        normalize_links: Convert relative links to absolute.

    Returns:
        Extracted content as a string in the specified format.
    """
    if quiet:
        logging.disable(logging.CRITICAL)

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    if path.is_dir():
        files = sorted(path.glob("**/*.md"))
        if not files:
            raise FileNotFoundError(f"No Markdown files found in: {input_path}")
        results = [_extract_file(f, **_build_kwargs(locals())) for f in files]
        combined = _combine_results(results, format)
    else:
        combined = _extract_file(path, **_build_kwargs(locals()))

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        ext = {"json": ".json", "text": ".txt", "html": ".html"}.get(format, ".txt")
        out_file = out_path / f"{path.stem}{ext}"
        out_file.write_text(combined, encoding="utf-8")
        logger.info("Output written to %s", out_file)

    if quiet:
        logging.disable(logging.NOTSET)

    return combined


def _build_kwargs(local_vars: dict[str, Any]) -> dict[str, Any]:
    """Build kwargs dict from local variables, excluding non-option args."""
    exclude = {
        "input_path",
        "path",
        "output_dir",
        "quiet",
        "files",
        "results",
        "combined",
        "f",
    }
    return {k: v for k, v in local_vars.items() if k not in exclude and not k.startswith("_")}


def _extract_file(
    file_path: Path,
    *,
    format: str = "json",
    heading_level: Optional[str] = None,
    sections: Optional[str] = None,
    include_frontmatter: bool = True,
    strip_html: bool = False,
    include_code_blocks: bool = True,
    include_toc: bool = False,
    flatten_lists: bool = False,
    section_separator: Optional[str] = None,
    normalize_links: bool = False,
) -> str:
    """Extract structured data from a single Markdown file."""
    content = file_path.read_text(encoding="utf-8")

    frontmatter, body = _split_frontmatter(content)
    parsed_sections = _parse_sections(body)

    # Filter by heading level
    if heading_level:
        levels = {int(lv.strip()) for lv in heading_level.split(",")}
        parsed_sections = [s for s in parsed_sections if s["level"] in levels]

    # Filter by section name
    if sections:
        names = [n.strip().lower() for n in sections.split(",")]
        parsed_sections = [
            s for s in parsed_sections if any(n in s["title"].lower() for n in names)
        ]

    # Strip HTML
    if strip_html:
        for s in parsed_sections:
            s["content"] = re.sub(r"<[^>]+>", "", s["content"])

    # Remove code blocks
    if not include_code_blocks:
        for s in parsed_sections:
            s["content"] = re.sub(r"```[\s\S]*?```", "", s["content"]).strip()

    # Flatten lists
    if flatten_lists:
        for s in parsed_sections:
            s["content"] = _flatten_lists(s["content"])

    # Normalize links
    if normalize_links:
        base_dir = str(file_path.parent)
        for s in parsed_sections:
            s["content"] = _normalize_links(s["content"], base_dir)

    # Build TOC
    toc = _build_toc(parsed_sections) if include_toc else None

    # Format output
    if format == "json":
        return _format_json(file_path, frontmatter, parsed_sections, toc, include_frontmatter)
    elif format == "html":
        return _format_html(file_path, frontmatter, parsed_sections, toc, include_frontmatter)
    else:
        return _format_text(
            file_path,
            frontmatter,
            parsed_sections,
            toc,
            include_frontmatter,
            section_separator,
        )


def _split_frontmatter(content: str) -> tuple[Optional[dict[str, Any]], str]:
    """Split YAML/TOML frontmatter from body."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                # Simple YAML-like parsing (key: value)
                fm: dict[str, Any] = {}
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        key, _, value = line.partition(":")
                        fm[key.strip()] = value.strip()
                return fm, parts[2].strip()
            except Exception:
                pass
    return None, content


def _parse_sections(body: str) -> list[dict[str, Any]]:
    """Parse Markdown body into sections based on headings."""
    sections: list[dict[str, Any]] = []
    current: Optional[dict[str, Any]] = None
    lines: list[str] = []

    for line in body.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            if current is not None:
                current["content"] = "\n".join(lines).strip()
                sections.append(current)
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            current = {"level": level, "title": title, "content": ""}
            lines = []
        else:
            lines.append(line)

    # Handle remaining content
    if current is not None:
        current["content"] = "\n".join(lines).strip()
        sections.append(current)
    elif lines:
        content = "\n".join(lines).strip()
        if content:
            sections.append({"level": 0, "title": "", "content": content})

    return sections


def _build_toc(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build table of contents from sections."""
    return [{"level": s["level"], "title": s["title"]} for s in sections if s["level"] > 0]


def _flatten_lists(content: str) -> str:
    """Flatten nested lists to a single level."""
    result = []
    for line in content.splitlines():
        match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if match:
            result.append(f"- {match.group(2)}")
        else:
            result.append(line)
    return "\n".join(result)


def _normalize_links(content: str, base_dir: str) -> str:
    """Convert relative links to absolute paths."""

    def replace_link(m: re.Match[str]) -> str:
        text, url = m.group(1), m.group(2)
        if not url.startswith(("http://", "https://", "#", "mailto:")):
            url = str(Path(base_dir) / url)
        return f"[{text}]({url})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, content)


def _format_json(
    file_path: Path,
    frontmatter: Optional[dict[str, Any]],
    sections: list[dict[str, Any]],
    toc: Optional[list[dict[str, Any]]],
    include_frontmatter: bool,
) -> str:
    """Format output as JSON."""
    result: dict[str, Any] = {"source": str(file_path)}
    if include_frontmatter and frontmatter:
        result["frontmatter"] = frontmatter
    if toc:
        result["toc"] = toc
    result["sections"] = sections
    return json.dumps(result, ensure_ascii=False, indent=2)


def _format_text(
    file_path: Path,
    frontmatter: Optional[dict[str, Any]],
    sections: list[dict[str, Any]],
    toc: Optional[list[dict[str, Any]]],
    include_frontmatter: bool,
    section_separator: Optional[str] = None,
) -> str:
    """Format output as plain text."""
    parts: list[str] = []

    if include_frontmatter and frontmatter:
        fm_lines = [f"{k}: {v}" for k, v in frontmatter.items()]
        parts.append("\n".join(fm_lines))

    if toc:
        toc_lines = ["Table of Contents:"]
        for entry in toc:
            indent = "  " * (entry["level"] - 1)
            toc_lines.append(f"{indent}- {entry['title']}")
        parts.append("\n".join(toc_lines))

    for s in sections:
        if section_separator and s["title"]:
            sep = section_separator.replace("%section-title%", s["title"])
            parts.append(sep)
        if s["title"]:
            parts.append(f"{'#' * s['level']} {s['title']}")
        if s["content"]:
            parts.append(s["content"])

    return "\n\n".join(parts)


def _format_html(
    file_path: Path,
    frontmatter: Optional[dict[str, Any]],
    sections: list[dict[str, Any]],
    toc: Optional[list[dict[str, Any]]],
    include_frontmatter: bool,
) -> str:
    """Format output as HTML."""
    parts: list[str] = ["<!DOCTYPE html>", "<html>", "<body>"]

    if include_frontmatter and frontmatter:
        parts.append("<dl>")
        for k, v in frontmatter.items():
            parts.append(f"  <dt>{k}</dt><dd>{v}</dd>")
        parts.append("</dl>")

    if toc:
        parts.append("<nav><ul>")
        for entry in toc:
            parts.append(f'  <li class="level-{entry["level"]}">{entry["title"]}</li>')
        parts.append("</ul></nav>")

    for s in sections:
        if s["title"]:
            tag = f"h{min(s['level'], 6)}"
            parts.append(f"<{tag}>{s['title']}</{tag}>")
        if s["content"]:
            paragraphs = s["content"].split("\n\n")
            for p in paragraphs:
                if p.strip():
                    parts.append(f"<p>{p.strip()}</p>")

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)


def _combine_results(results: list[str], format: str) -> str:
    """Combine multiple file results."""
    if format == "json":
        parsed = [json.loads(r) for r in results]
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    return "\n\n---\n\n".join(results)
