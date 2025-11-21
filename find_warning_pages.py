from pathlib import Path


def main() -> None:
    """
    Scan the Embedding directory for HTML files containing the yellow warning banner.

    We detect pages that include either the warning emoji (⚠️) or the CSS class
    `warning-box`, which correspond to the “important logo + yellow block” pattern.
    """
    root = Path("Embedding")
    if not root.exists():
        raise SystemExit("Embedding/ directory not found from current working directory.")

    needles = ("⚠️", "warning-box")
    matches: list[Path] = []

    for html_file in root.rglob("*.html"):
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        if any(token in content for token in needles):
            matches.append(html_file)

    for path in sorted(matches):
        print(path.as_posix())


if __name__ == "__main__":
    main()

