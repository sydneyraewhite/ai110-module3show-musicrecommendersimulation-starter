"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    # When run as a module: python -m src.main
    from src.recommender import load_songs, recommend_songs
except ImportError:
    # When run directly from inside src/: python main.py
    from recommender import load_songs, recommend_songs


def print_recommendations(user_prefs: dict, recommendations: list) -> None:
    """Print recommendations in a clean, readable terminal layout."""
    profile = ", ".join(f"{key}={value}" for key, value in user_prefs.items())

    print()
    print("=" * 56)
    print(f"  🎵  Top {len(recommendations)} recommendations")
    print(f"      for taste profile: {profile}")
    print("=" * 56)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print()
        print(f"  {rank}. {song['title']}  —  {song['artist']}")
        print(f"     score: {score:.2f}")
        print("     why:")
        for reason in explanation.split("; "):
            print(f"       • {reason}")

    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)
    print_recommendations(user_prefs, recommendations)


if __name__ == "__main__":
    main()
