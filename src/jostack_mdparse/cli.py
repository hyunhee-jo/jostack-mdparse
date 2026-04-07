"""CLI entry point for jostack-mdparse."""

from __future__ import annotations

import argparse
import sys

from jostack_mdparse import __version__, extract


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="jostack-mdparse",
        description="Markdown file parser and structured extraction tool",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # extract command
    extract_parser = subparsers.add_parser(
        "extract", help="Parse Markdown and output structured data"
    )
    _add_common_args(extract_parser)
    _add_extract_options(extract_parser)

    # toc command
    toc_parser = subparsers.add_parser("toc", help="Print the table of contents (heading tree)")
    _add_common_args(toc_parser)
    toc_parser.add_argument(
        "--heading-level",
        default=None,
        help="Filter by heading levels (comma-separated)",
    )

    # meta command
    meta_parser = subparsers.add_parser("meta", help="Print frontmatter metadata as JSON")
    _add_common_args(meta_parser)

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "extract":
        result = extract(
            args.input,
            output_dir=args.output_dir,
            format=args.format,
            quiet=args.quiet,
            heading_level=args.heading_level,
            sections=args.sections,
            include_frontmatter=args.include_frontmatter,
            strip_html=args.strip_html,
            include_code_blocks=args.include_code_blocks,
            include_toc=args.include_toc,
            flatten_lists=args.flatten_lists,
            section_separator=args.section_separator,
            normalize_links=args.normalize_links,
        )
        print(result)

    elif args.command == "toc":
        result = extract(
            args.input,
            format=args.format,
            quiet=args.quiet,
            include_toc=True,
            heading_level=args.heading_level,
        )
        print(result)

    elif args.command == "meta":
        result = extract(
            args.input,
            format="json",
            quiet=args.quiet,
            include_frontmatter=True,
        )
        print(result)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments shared across all commands."""
    parser.add_argument("input", help="Path to Markdown file or directory")
    parser.add_argument(
        "-f",
        "--format",
        default="json",
        choices=["json", "text", "html"],
        help="Output format (default: json)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress console logging output",
    )


def _add_extract_options(parser: argparse.ArgumentParser) -> None:
    """Add extract-specific options from options.json."""
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory")
    parser.add_argument(
        "--heading-level", default=None, help="Filter by heading levels (comma-separated)"
    )
    parser.add_argument(
        "-s", "--sections", default=None, help="Extract sections by heading text (comma-separated)"
    )
    parser.add_argument(
        "--include-frontmatter", action="store_true", default=True, help="Include frontmatter"
    )
    parser.add_argument(
        "--no-include-frontmatter", action="store_false", dest="include_frontmatter"
    )
    parser.add_argument("--strip-html", action="store_true", default=False, help="Strip HTML tags")
    parser.add_argument(
        "--include-code-blocks", action="store_true", default=True, help="Include code blocks"
    )
    parser.add_argument(
        "--no-include-code-blocks", action="store_false", dest="include_code_blocks"
    )
    parser.add_argument(
        "--include-toc", action="store_true", default=False, help="Add table of contents"
    )
    parser.add_argument(
        "--flatten-lists", action="store_true", default=False, help="Flatten nested lists"
    )
    parser.add_argument(
        "--section-separator", default=None, help="Section separator (use %%section-title%%)"
    )
    parser.add_argument(
        "--normalize-links", action="store_true", default=False, help="Normalize relative links"
    )
