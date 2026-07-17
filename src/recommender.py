import csv
from operator import itemgetter
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# --- Scoring weights (tune these in your "Experiments You Tried" section) ---
W_GENRE = 2.0      # points for an exact genre match
W_MOOD = 1.5       # points for an exact mood match
W_ENERGY = 2.0     # max points for a perfect energy match (scaled by closeness)
W_ACOUSTIC = 0.5   # points when acoustic-ness matches the user's preference


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def proximity_score(value: float, target: float) -> float:
    """
    Score a 0-1 numeric feature by CLOSENESS to a target, not by magnitude.
    Returns 1.0 at a perfect match, falling linearly to 0.0 at maximum distance.
    This is what lets a low-energy user be rewarded for calm songs instead of
    always preferring the loudest track.
    """
    return 1.0 - abs(value - target)


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score one Song against a UserProfile. Returns (score, reasons)."""
        score = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            score += W_GENRE
            reasons.append(f"genre match: {song.genre} (+{W_GENRE:.1f})")

        if song.mood == user.favorite_mood:
            score += W_MOOD
            reasons.append(f"mood match: {song.mood} (+{W_MOOD:.1f})")

        energy_fit = proximity_score(song.energy, user.target_energy)
        energy_points = W_ENERGY * energy_fit
        score += energy_points
        reasons.append(
            f"energy {song.energy} vs target {user.target_energy} (+{energy_points:.2f})"
        )

        is_acoustic = song.acousticness > 0.5
        if is_acoustic == user.likes_acoustic:
            score += W_ACOUSTIC
            reasons.append(f"acoustic preference match (+{W_ACOUSTIC:.1f})")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Score every song, rank highest-first, and return the top k."""
        ranked = sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Produce a human-readable reason this song was recommended."""
        score, reasons = self._score(user, song)
        if reasons:
            return f"{song.title} (score {score:.2f}): " + "; ".join(reasons)
        return f"{song.title} (score {score:.2f}): a broad match for your taste"


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dicts, converting each numeric
    column to the right type so scoring math works later.

    - int columns:   id, tempo_bpm         (whole numbers)
    - float columns: energy, valence,       (continuous 0-1 audio features)
                     danceability, acousticness
    Text columns (title, artist, genre, mood) are left as strings.
    Required by src/main.py
    """
    int_cols = {"id", "tempo_bpm"}
    float_cols = {"energy", "valence", "danceability", "acousticness"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for col in int_cols:
                if row.get(col, "") != "":
                    row[col] = int(row[col])
            for col in float_cols:
                if row.get(col, "") != "":
                    row[col] = float(row[col])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song (dict) against user preferences (dict).
    Accepts flexible preference keys so it works with main.py's profile
    ({"genre", "mood", "energy"}) and richer profiles alike.
    Returns (score, reasons).
    """
    score = 0.0
    reasons: List[str] = []

    fav_genre = user_prefs.get("genre", user_prefs.get("favorite_genre"))
    if fav_genre is not None and song.get("genre") == fav_genre:
        score += W_GENRE
        reasons.append(f"genre match: {song['genre']} (+{W_GENRE:.1f})")

    fav_mood = user_prefs.get("mood", user_prefs.get("favorite_mood"))
    if fav_mood is not None and song.get("mood") == fav_mood:
        score += W_MOOD
        reasons.append(f"mood match: {song['mood']} (+{W_MOOD:.1f})")

    target_energy = user_prefs.get("energy", user_prefs.get("target_energy"))
    if target_energy is not None:
        energy_fit = proximity_score(float(song["energy"]), float(target_energy))
        energy_points = W_ENERGY * energy_fit
        score += energy_points
        reasons.append(
            f"energy {song['energy']} vs target {target_energy} (+{energy_points:.2f})"
        )

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        is_acoustic = float(song["acousticness"]) > 0.5
        if is_acoustic == likes_acoustic:
            score += W_ACOUSTIC
            reasons.append(f"acoustic preference match (+{W_ACOUSTIC:.1f})")

    return score, reasons


def _judge(user_prefs: Dict, song: Dict) -> Tuple[Dict, float, str]:
    """Score one song and package it as a (song, score, explanation) row."""
    score, reasons = score_song(user_prefs, song)
    explanation = "; ".join(reasons) if reasons else "a broad match for your taste"
    return song, score, explanation


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """
    Scores and ranks all songs, returning the top k as
    (song_dict, score, explanation) tuples.
    Required by src/main.py
    """
    # 1. JUDGE every song in the catalog with score_song (via _judge).
    scored = (_judge(user_prefs, song) for song in songs)
    # 2. RANK by score (index 1), highest first, and 3. keep the top k.
    return sorted(scored, key=itemgetter(1), reverse=True)[:k]
