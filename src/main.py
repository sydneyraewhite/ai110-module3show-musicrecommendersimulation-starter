"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You can switch ranking modes (the Strategy pattern) from the command line:

    python -m src.main                 # show the profile under every mode
    python -m src.main energy-focused  # show just one mode
    python -m src.main genre-first
    python -m src.main mood-first
    python -m src.main balanced

Add "diverse" to spread out artists/genres in the results, e.g.

    python -m src.main balanced diverse
"""

import sys
import textwrap

try:
    # When run as a module: python -m src.main
    from src.recommender import load_songs, recommend_songs, STRATEGIES
except ImportError:
    # When run directly from inside src/: python main.py
    from recommender import load_songs, recommend_songs, STRATEGIES

# Use the `tabulate` library for a nicer grid if it is installed, otherwise fall
# back to the pure-Python ASCII table below (no extra install needed).
try:
    from tabulate import tabulate
    _HAS_TABULATE = True
except ImportError:
    _HAS_TABULATE = False

REASON_WIDTH = 46  # how wide the "Why" column wraps before breaking to a new line


def _reason_lines(explanation: str, width: int = REASON_WIDTH) -> list:
    """Turn a '; '-joined explanation into wrapped, bulleted lines for one cell."""
    lines = []
    for reason in explanation.split("; "):
        wrapped = textwrap.wrap(reason, width=width) or [""]
        lines.append("• " + wrapped[0])
        lines.extend("  " + cont for cont in wrapped[1:])  # indent wrapped continuations
    return lines


def _ascii_table(headers: list, rows: list) -> str:
    """Render a simple box-drawing table that supports multi-line cells."""
    def cell_lines(cell):
        return str(cell).split("\n")

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            for line in cell_lines(cell):
                widths[i] = max(widths[i], len(line))

    def rule(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def render(row):
        cells = [cell_lines(c) for c in row]
        height = max(len(c) for c in cells)
        out = []
        for h in range(height):
            parts = [
                " " + (cells[i][h] if h < len(cells[i]) else "").ljust(widths[i]) + " "
                for i in range(len(headers))
            ]
            out.append("│" + "│".join(parts) + "│")
        return "\n".join(out)

    parts = [rule("┌", "┬", "┐"), render(headers), rule("├", "┼", "┤")]
    for row in rows:
        parts.append(render(row))
        parts.append(rule("├", "┼", "┤"))
    parts[-1] = rule("└", "┴", "┘")  # bottom border instead of a separator
    return "\n".join(parts)


def print_recommendations(user_prefs: dict, recommendations: list, mode: str = "") -> None:
    """Print recommendations as a formatted table, including the reasons per score."""
    profile = ", ".join(f"{key}={value}" for key, value in user_prefs.items())

    print()
    print(f"🎵  Top {len(recommendations)} recommendations")
    if mode:
        print(f"    mode: {mode}")
    print(f"    taste profile: {profile}")
    print()

    headers = ["#", "Song", "Artist", "Score", "Why (reasons add up to the score)"]
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        why = "\n".join(_reason_lines(explanation))
        rows.append([str(rank), song["title"], song["artist"], f"{score:.2f}", why])

    if _HAS_TABULATE:
        print(tabulate(
            rows,
            headers=headers,
            tablefmt="grid",
            colalign=("center", "left", "left", "right", "left"),
        ))
    else:
        print(_ascii_table(headers, rows))
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    # Read command-line arguments. "diverse" (anywhere) turns on the diversity
    # penalty; any other argument is treated as the ranking mode to use.
    args = [a.lower() for a in sys.argv[1:]]
    diversity = "diverse" in args
    mode_args = [a for a in args if a != "diverse"]
    arg = mode_args[0] if mode_args else None

    # With no mode given we show every mode so the difference is easy to see.
    if arg in STRATEGIES:
        chosen = {arg: STRATEGIES[arg]}
    else:
        if arg is not None:
            print(f"Unknown mode '{arg}'. Options: {', '.join(STRATEGIES)}. Showing all.")
        chosen = STRATEGIES

    for strategy in chosen.values():
        recommendations = recommend_songs(
            user_prefs, songs, k=5, strategy=strategy, diversity=diversity
        )
        label = f"{strategy.name}{' + diversity' if diversity else ''}"
        print_recommendations(user_prefs, recommendations, mode=label)


if __name__ == "__main__":
    main()
