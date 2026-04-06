"""Unit tests for markdown_extract.extract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from markdown_extract.extract import (
    _flatten_lists,
    _normalize_links,
    _parse_sections,
    _split_frontmatter,
    extract,
)


class TestSplitFrontmatter:
    """Tests for YAML frontmatter splitting."""

    def test_with_frontmatter(self) -> None:
        content = "---\ntitle: Hello\nauthor: Test\n---\n\n# Body"
        fm, body = _split_frontmatter(content)
        assert fm is not None
        assert fm["title"] == "Hello"
        assert fm["author"] == "Test"
        assert body == "# Body"

    def test_without_frontmatter(self) -> None:
        content = "# No Frontmatter\n\nJust text."
        fm, body = _split_frontmatter(content)
        assert fm is None
        assert body == content

    def test_empty_content(self) -> None:
        fm, body = _split_frontmatter("")
        assert fm is None
        assert body == ""


class TestParseSections:
    """Tests for section parsing."""

    def test_multiple_headings(self) -> None:
        body = "# H1\n\nPara1\n\n## H2\n\nPara2\n\n### H3\n\nPara3"
        sections = _parse_sections(body)
        assert len(sections) == 3
        assert sections[0]["level"] == 1
        assert sections[0]["title"] == "H1"
        assert "Para1" in sections[0]["content"]
        assert sections[1]["level"] == 2
        assert sections[2]["level"] == 3

    def test_no_headings(self) -> None:
        body = "Just plain text\nwith no headings."
        sections = _parse_sections(body)
        assert len(sections) == 1
        assert sections[0]["level"] == 0
        assert sections[0]["title"] == ""

    def test_empty_body(self) -> None:
        sections = _parse_sections("")
        assert len(sections) == 0


class TestFlattenLists:
    """Tests for list flattening."""

    def test_nested_list(self) -> None:
        content = "- Item 1\n  - Sub A\n    - Sub Sub\n- Item 2"
        result = _flatten_lists(content)
        assert "- Item 1" in result
        assert "- Sub A" in result
        assert "- Sub Sub" in result
        assert "  -" not in result

    def test_no_lists(self) -> None:
        content = "Just text, no lists."
        result = _flatten_lists(content)
        assert result == content


class TestNormalizeLinks:
    """Tests for link normalization."""

    def test_relative_link(self) -> None:
        content = "[Guide](./docs/guide.md)"
        result = _normalize_links(content, "/project")
        assert "project" in result
        assert "guide.md" in result

    def test_absolute_link_unchanged(self) -> None:
        content = "[GitHub](https://github.com)"
        result = _normalize_links(content, "/project")
        assert result == content

    def test_anchor_link_unchanged(self) -> None:
        content = "[Section](#section)"
        result = _normalize_links(content, "/project")
        assert result == content


class TestExtract:
    """Integration tests for the extract function."""

    def test_basic_json(self, sample_md: Path) -> None:
        result = extract(sample_md, format="json", quiet=True)
        parsed = json.loads(result)
        assert parsed["source"] == str(sample_md)
        assert "frontmatter" in parsed
        assert parsed["frontmatter"]["title"] == "Sample Document"
        assert len(parsed["sections"]) > 0

    def test_basic_text(self, sample_md: Path) -> None:
        result = extract(sample_md, format="text", quiet=True)
        assert "Introduction" in result
        assert "Getting Started" in result

    def test_basic_html(self, sample_md: Path) -> None:
        result = extract(sample_md, format="html", quiet=True)
        assert "<html>" in result
        assert "<h1>Introduction</h1>" in result

    def test_heading_level_filter(self, sample_md: Path) -> None:
        result = extract(sample_md, format="json", quiet=True, heading_level="1")
        parsed = json.loads(result)
        for section in parsed["sections"]:
            assert section["level"] == 1

    def test_sections_filter(self, sample_md: Path) -> None:
        result = extract(sample_md, format="json", quiet=True, sections="Usage")
        parsed = json.loads(result)
        assert len(parsed["sections"]) == 1
        assert parsed["sections"][0]["title"] == "Usage"

    def test_strip_html(self, sample_md: Path) -> None:
        result = extract(sample_md, format="text", quiet=True, strip_html=True)
        assert "<strong>" not in result

    def test_exclude_code_blocks(self, sample_md: Path) -> None:
        result = extract(sample_md, format="text", quiet=True, include_code_blocks=False)
        assert "from markdown_extract" not in result

    def test_include_toc(self, sample_md: Path) -> None:
        result = extract(sample_md, format="json", quiet=True, include_toc=True)
        parsed = json.loads(result)
        assert "toc" in parsed
        assert len(parsed["toc"]) > 0

    def test_no_frontmatter(self, sample_md: Path) -> None:
        result = extract(sample_md, format="json", quiet=True, include_frontmatter=False)
        parsed = json.loads(result)
        assert "frontmatter" not in parsed

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            extract(tmp_path / "nonexistent.md")

    def test_output_dir(self, sample_md: Path, tmp_path: Path) -> None:
        extract(sample_md, format="json", quiet=True, output_dir=str(tmp_path))
        output_files = list(tmp_path.glob("*.json"))
        assert len(output_files) == 1

    def test_directory_input(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("# A\n\nContent A", encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n\nContent B", encoding="utf-8")
        result = extract(tmp_path, format="json", quiet=True)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_flatten_lists_option(self, sample_md: Path) -> None:
        result = extract(sample_md, format="text", quiet=True, flatten_lists=True)
        assert result.count("  -") == 0  # No indented list items

    def test_section_separator(self, sample_md: Path) -> None:
        result = extract(
            sample_md, format="text", quiet=True, section_separator="=== %section-title% ==="
        )
        assert "=== Introduction ===" in result
