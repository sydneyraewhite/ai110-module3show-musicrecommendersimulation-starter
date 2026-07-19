"""
Adversarial / edge-case harness for the Music Recommender.

Each profile below is designed to probe a specific weakness in the scoring
logic (see the `attacks` note on each entry). Run it to observe the top-5
results in the terminal and capture output for the "Experiments" writeup:

    python -m src.adversarial
"""

try:
    from src.recommender import load_songs, recommend_songs
    from src.main import print_recommendations
except ImportError:
    from recommender import load_songs, recommend_songs
    from main import print_recommendations


# (label, why-it's-adversarial, profile)
ADVERSARIAL_PROFILES = [
    (
        "Conflicting energy vs. mood",
        "Mood and energy are scored independently, so a 'sad' + high-energy "
        "profile can't be satisfied by any one song and yields incoherent recs.",
        {"genre": "pop", "mood": "sad", "energy": 0.9},
    ),
    (
        "Energy above range (5.0) — no clamping",
        "proximity_score goes strongly negative; total scores invert and go < 0.",
        {"genre": "rock", "energy": 5.0},
    ),
    (
        "Energy below range (-1.0) — no clamping",
        "Negative target; every energy term is negative, ranking is distorted.",
        {"genre": "rock", "energy": -1.0},
    ),
    (
        "Typo / wrong casing — silent zero",
        "Exact, case-sensitive matching means these contribute 0 for every song.",
        {"genre": "Pop", "mood": "Happy"},
    ),
    (
        "Unknown genre + mood — silent zero",
        "Values not in the catalog; genre/mood add nothing, no warning is raised.",
        {"genre": "k-pop", "mood": "melancholy"},
    ),
    (
        "Empty profile",
        "No signal at all: every song scores 0.0 and ranking falls back to CSV order.",
        {},
    ),
    (
        "Acoustic freebie (False)",
        "Non-acoustic + likes_acoustic=False ALSO earns +0.5, so nearly every song "
        "collects this point — it barely discriminates.",
        {"likes_acoustic": False},
    ),
    (
        "Weight collision (genre == max energy == 2.0)",
        "Perfect genre match w/ terrible energy ties a perfect energy match w/ wrong genre.",
        {"genre": "rock", "energy": 0.0},
    ),
    (
        "Type confusion — likes_acoustic as string",
        "'yes' is truthy but == comparison against a bool is always False; term vanishes.",
        {"likes_acoustic": "yes"},
    ),
]


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for i, (label, why, profile) in enumerate(ADVERSARIAL_PROFILES, start=1):
        print("\n" + "#" * 60)
        print(f"# ADVERSARIAL PROFILE {i}: {label}")
        print(f"# attacks: {why}")
        print("#" * 60)
        try:
            recs = recommend_songs(profile, songs, k=5)
            print_recommendations(profile, recs)
        except Exception as exc:  # noqa: BLE001 — we WANT to observe crashes
            print(f"\n  ⚠️  raised {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
