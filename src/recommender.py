import csv
from operator import itemgetter
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# --- Scoring weights (tune these in your "Experiments You Tried" section) ---
W_GENRE = 2.0      # points for an exact genre match
W_MOOD = 1.5       # points for an exact mood match
W_ENERGY = 2.0     # max points for a perfect energy match (scaled by closeness)
W_ACOUSTIC = 0.5   # points when acoustic-ness matches the user's preference

# --- Weights for the newer, more detailed attributes ---
W_POPULARITY = 1.0        # max points, scaled by how well popularity fits the user's lean
W_DECADE = 1.0            # points for an exact release-decade match
W_MOOD_TAGS = 0.75        # points per detailed mood tag the song shares with the user
W_LANGUAGE = 1.0          # points for an exact language match
W_INSTRUMENTAL = 0.5      # points when instrumental-ness matches the user's preference
W_EXPLICIT_PENALTY = -1.0  # penalty for an explicit song when the user opts out

# --- Diversity penalty ---
# Applied while building the top-k list (not per-song), to avoid stacking the
# results with the same artist or genre. The rule: each time a candidate would
# repeat an artist/genre already chosen for the list, subtract a penalty from its
# score. Repeating an artist is penalized harder than repeating a genre.
PENALTY_SAME_ARTIST = 1.5   # subtracted per already-chosen song by the same artist
PENALTY_SAME_GENRE = 0.75   # subtracted per already-chosen song in the same genre


# --- Ranking strategies (Strategy pattern) ---
# A strategy is just a named bundle of weights. The scoring logic stays the same;
# swapping the strategy object changes what the recommender emphasizes. The default
# weights above define the "Balanced" mode, so old callers behave exactly as before.
@dataclass(frozen=True)
class RankingStrategy:
    """One interchangeable set of scoring weights ('mode') the recommender can use."""
    name: str
    w_genre: float = W_GENRE
    w_mood: float = W_MOOD
    w_energy: float = W_ENERGY
    w_acoustic: float = W_ACOUSTIC
    w_popularity: float = W_POPULARITY
    w_decade: float = W_DECADE
    w_mood_tags: float = W_MOOD_TAGS
    w_language: float = W_LANGUAGE
    w_instrumental: float = W_INSTRUMENTAL
    w_explicit_penalty: float = W_EXPLICIT_PENALTY


# Concrete modes a user can switch between. Each keeps the newer-attribute weights
# at their defaults and only re-tilts the three main axes (genre / mood / energy).
BALANCED = RankingStrategy(name="Balanced")
GENRE_FIRST = RankingStrategy(name="Genre-First", w_genre=5.0, w_mood=1.0, w_energy=1.0)
MOOD_FIRST = RankingStrategy(name="Mood-First", w_genre=1.0, w_mood=5.0, w_energy=1.0)
ENERGY_FOCUSED = RankingStrategy(name="Energy-Focused", w_genre=1.0, w_mood=0.5, w_energy=5.0)

# Look up a strategy by a simple lowercase key (handy for a CLI or a menu).
STRATEGIES: Dict[str, RankingStrategy] = {
    "balanced": BALANCED,
    "genre-first": GENRE_FIRST,
    "mood-first": MOOD_FIRST,
    "energy-focused": ENERGY_FOCUSED,
}


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
    # Newer, more detailed attributes (default so older callers/tests still work).
    popularity: int = 0                              # 0-100 listening popularity
    release_decade: int = 0                          # e.g. 1990, 2010, 2020
    mood_tags: List[str] = field(default_factory=list)  # detailed secondary moods
    language: str = ""                               # english, instrumental, ...
    instrumentalness: float = 0.0                    # 0.0-1.0, how instrumental
    explicit: bool = False                           # explicit lyrics flag


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
    # Preferences for the newer attributes (all optional; None = "don't care").
    popularity_pref: Optional[str] = None            # "high" or "low"
    favorite_decade: Optional[int] = None            # e.g. 2010
    mood_tags: List[str] = field(default_factory=list)  # detailed moods to reward
    language: Optional[str] = None                   # preferred language
    likes_instrumental: Optional[bool] = None        # True/False/None
    allow_explicit: Optional[bool] = None            # False to penalize explicit songs


def proximity_score(value: float, target: float) -> float:
    """Score a 0-1 feature by closeness to a target (1.0 = exact match, down to 0.0)."""
    return 1.0 - abs(value - target)


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], strategy: RankingStrategy = BALANCED):
        self.songs = songs
        self.strategy = strategy  # the ranking "mode"; defaults to Balanced

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Score one Song against a UserProfile using the active strategy's weights."""
        w = self.strategy
        score = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            score += w.w_genre
            reasons.append(f"genre match: {song.genre} (+{w.w_genre:.1f})")

        if song.mood == user.favorite_mood:
            score += w.w_mood
            reasons.append(f"mood match: {song.mood} (+{w.w_mood:.1f})")

        energy_fit = proximity_score(song.energy, user.target_energy)
        energy_points = w.w_energy * energy_fit
        score += energy_points
        reasons.append(
            f"energy {song.energy} vs target {user.target_energy} (+{energy_points:.2f})"
        )

        is_acoustic = song.acousticness > 0.5
        if is_acoustic == user.likes_acoustic:
            score += w.w_acoustic
            reasons.append(f"acoustic preference match (+{w.w_acoustic:.1f})")

        # --- Newer, more detailed attributes ---
        if user.popularity_pref is not None:
            fit = song.popularity / 100.0
            if user.popularity_pref == "low":
                fit = 1.0 - fit
            pop_points = w.w_popularity * fit
            score += pop_points
            reasons.append(
                f"popularity {song.popularity} ({user.popularity_pref}) (+{pop_points:.2f})"
            )

        if user.favorite_decade is not None and song.release_decade == user.favorite_decade:
            score += w.w_decade
            reasons.append(f"decade match: {song.release_decade}s (+{w.w_decade:.1f})")

        if user.mood_tags:
            matched = [t for t in song.mood_tags if t in user.mood_tags]
            if matched:
                tag_points = w.w_mood_tags * len(matched)
                score += tag_points
                reasons.append(f"mood tags match: {', '.join(matched)} (+{tag_points:.2f})")

        if user.language is not None and song.language == user.language:
            score += w.w_language
            reasons.append(f"language match: {song.language} (+{w.w_language:.1f})")

        if user.likes_instrumental is not None:
            is_instrumental = song.instrumentalness > 0.5
            if is_instrumental == user.likes_instrumental:
                score += w.w_instrumental
                reasons.append(f"instrumental preference match (+{w.w_instrumental:.1f})")

        if user.allow_explicit is False and song.explicit:
            score += w.w_explicit_penalty
            reasons.append(f"explicit content penalty ({w.w_explicit_penalty:.1f})")

        return score, reasons

    def recommend(
        self,
        user: UserProfile,
        k: int = 5,
        diversity: bool = False,
        artist_penalty: float = PENALTY_SAME_ARTIST,
        genre_penalty: float = PENALTY_SAME_GENRE,
    ) -> List[Song]:
        """Score every song, rank highest-first, and return the top k.

        With `diversity=True`, greedily build the list while penalizing repeats of an
        artist/genre already chosen, so the top k are not dominated by one artist.
        """
        scored = [(song, self._score(user, song)[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)

        if not diversity:
            return [song for song, _ in scored[:k]]

        selected: List[Song] = []
        remaining = list(scored)
        while remaining and len(selected) < k:
            best_i, best_adj = 0, None
            for i, (song, base) in enumerate(remaining):
                artist_repeats = sum(1 for s in selected if s.artist == song.artist)
                genre_repeats = sum(1 for s in selected if s.genre == song.genre)
                adjusted = base - artist_penalty * artist_repeats - genre_penalty * genre_repeats
                if best_adj is None or adjusted > best_adj:
                    best_i, best_adj = i, adjusted
            song, _ = remaining.pop(best_i)
            selected.append(song)
        return selected

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Produce a human-readable reason this song was recommended."""
        score, reasons = self._score(user, song)
        if reasons:
            return f"{song.title} (score {score:.2f}): " + "; ".join(reasons)
        return f"{song.title} (score {score:.2f}): a broad match for your taste"


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV into a list of dicts, casting numeric columns to int/float."""
    int_cols = {"id", "tempo_bpm", "popularity", "release_decade"}
    float_cols = {"energy", "valence", "danceability", "acousticness", "instrumentalness"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for col in int_cols:
                if row.get(col, "") != "":
                    row[col] = int(row[col])
            for col in float_cols:
                if row.get(col, "") != "":
                    row[col] = float(row[col])
            # Detailed mood tags are stored as a "tag1;tag2" string -> list.
            if row.get("mood_tags"):
                row["mood_tags"] = [t.strip() for t in row["mood_tags"].split(";") if t.strip()]
            else:
                row["mood_tags"] = []
            # Explicit is a "True"/"False" string -> bool.
            if "explicit" in row:
                row["explicit"] = str(row["explicit"]).strip().lower() == "true"
            songs.append(row)
    return songs


def score_song(
    user_prefs: Dict, song: Dict, strategy: RankingStrategy = BALANCED
) -> Tuple[float, List[str]]:
    """Score one song dict against user preferences using a strategy; returns (score, reasons)."""
    w = strategy
    score = 0.0
    reasons: List[str] = []

    fav_genre = user_prefs.get("genre", user_prefs.get("favorite_genre"))
    if fav_genre is not None and song.get("genre") == fav_genre:
        score += w.w_genre
        reasons.append(f"genre match: {song['genre']} (+{w.w_genre:.1f})")

    fav_mood = user_prefs.get("mood", user_prefs.get("favorite_mood"))
    if fav_mood is not None and song.get("mood") == fav_mood:
        score += w.w_mood
        reasons.append(f"mood match: {song['mood']} (+{w.w_mood:.1f})")

    target_energy = user_prefs.get("energy", user_prefs.get("target_energy"))
    if target_energy is not None:
        energy_fit = proximity_score(float(song["energy"]), float(target_energy))
        energy_points = w.w_energy * energy_fit
        score += energy_points
        reasons.append(
            f"energy {song['energy']} vs target {target_energy} (+{energy_points:.2f})"
        )

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        is_acoustic = float(song["acousticness"]) > 0.5
        if is_acoustic == likes_acoustic:
            score += w.w_acoustic
            reasons.append(f"acoustic preference match (+{w.w_acoustic:.1f})")

    # --- Newer, more detailed attributes ---
    popularity_pref = user_prefs.get("popularity_pref")
    if popularity_pref is not None and song.get("popularity") is not None:
        fit = float(song["popularity"]) / 100.0
        if popularity_pref == "low":
            fit = 1.0 - fit
        pop_points = w.w_popularity * fit
        score += pop_points
        reasons.append(
            f"popularity {song['popularity']} ({popularity_pref}) (+{pop_points:.2f})"
        )

    fav_decade = user_prefs.get("decade", user_prefs.get("favorite_decade"))
    if fav_decade is not None and song.get("release_decade") == fav_decade:
        score += w.w_decade
        reasons.append(f"decade match: {song['release_decade']}s (+{w.w_decade:.1f})")

    wanted_tags = user_prefs.get("mood_tags")
    if wanted_tags:
        song_tags = song.get("mood_tags") or []
        if isinstance(song_tags, str):  # tolerate an un-parsed raw string
            song_tags = [t.strip() for t in song_tags.split(";") if t.strip()]
        matched = [t for t in song_tags if t in wanted_tags]
        if matched:
            tag_points = w.w_mood_tags * len(matched)
            score += tag_points
            reasons.append(f"mood tags match: {', '.join(matched)} (+{tag_points:.2f})")

    fav_language = user_prefs.get("language")
    if fav_language is not None and song.get("language") == fav_language:
        score += w.w_language
        reasons.append(f"language match: {song['language']} (+{w.w_language:.1f})")

    likes_instrumental = user_prefs.get("likes_instrumental")
    if likes_instrumental is not None and song.get("instrumentalness") is not None:
        is_instrumental = float(song["instrumentalness"]) > 0.5
        if is_instrumental == likes_instrumental:
            score += w.w_instrumental
            reasons.append(f"instrumental preference match (+{w.w_instrumental:.1f})")

    if user_prefs.get("allow_explicit") is False and song.get("explicit"):
        score += w.w_explicit_penalty
        reasons.append(f"explicit content penalty ({w.w_explicit_penalty:.1f})")

    return score, reasons


def _judge(
    user_prefs: Dict, song: Dict, strategy: RankingStrategy = BALANCED
) -> Tuple[Dict, float, str]:
    """Score one song and package it as a (song, score, explanation) row."""
    score, reasons = score_song(user_prefs, song, strategy)
    explanation = "; ".join(reasons) if reasons else "a broad match for your taste"
    return song, score, explanation


def _select_diverse(
    scored: List[Tuple[Dict, float, str]],
    k: int,
    artist_penalty: float,
    genre_penalty: float,
) -> List[Tuple[Dict, float, str]]:
    """Greedily pick k songs, penalizing repeats of an already-chosen artist/genre.

    Each round we re-score every remaining candidate against the songs already in
    the list: subtract `artist_penalty` for every prior pick by the same artist and
    `genre_penalty` for every prior pick in the same genre, then take the best. This
    lets a slightly lower-scoring but fresh song beat a repeat of a top artist.
    """
    remaining = list(scored)
    selected: List[Tuple[Dict, float, str]] = []

    while remaining and len(selected) < k:
        best_i, best_adj, best_penalty = 0, None, 0.0
        for i, (song, base, _expl) in enumerate(remaining):
            artist_repeats = sum(1 for s, _, _ in selected if s.get("artist") == song.get("artist"))
            genre_repeats = sum(1 for s, _, _ in selected if s.get("genre") == song.get("genre"))
            penalty = artist_penalty * artist_repeats + genre_penalty * genre_repeats
            adjusted = base - penalty
            if best_adj is None or adjusted > best_adj:
                best_i, best_adj, best_penalty = i, adjusted, penalty

        song, base, expl = remaining.pop(best_i)
        if best_penalty > 0:
            expl = f"{expl}; diversity penalty (-{best_penalty:.2f})"
        selected.append((song, best_adj, expl))

    return selected


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: RankingStrategy = BALANCED,
    diversity: bool = False,
    artist_penalty: float = PENALTY_SAME_ARTIST,
    genre_penalty: float = PENALTY_SAME_GENRE,
) -> List[Tuple[Dict, float, str]]:
    """Judge every song with the chosen strategy, then return the top k (best first).

    Pass a different `strategy` (e.g. GENRE_FIRST, ENERGY_FOCUSED) to switch modes.
    Set `diversity=True` to spread out artists/genres in the top k (see _select_diverse).
    """
    # 1. JUDGE every song in the catalog with score_song (via _judge).
    scored = [_judge(user_prefs, song, strategy) for song in songs]
    # 2. RANK by score (index 1), highest first.
    scored.sort(key=itemgetter(1), reverse=True)
    # 3. Keep the top k — either straight, or with the diversity re-rank.
    if diversity:
        return _select_diverse(scored, k, artist_penalty, genre_penalty)
    return scored[:k]
