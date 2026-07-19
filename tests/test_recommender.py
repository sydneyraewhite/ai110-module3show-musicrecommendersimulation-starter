from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Diversity penalty tests ---

def make_artist_cluster_recommender() -> Recommender:
    """Two high-scoring songs by the same artist, plus one by a different artist."""
    common = dict(
        genre="pop", mood="happy", tempo_bpm=120,
        valence=0.9, danceability=0.8, acousticness=0.2,
    )
    songs = [
        Song(id=1, title="Echo One", artist="Neon Echo", energy=0.80, **common),
        Song(id=2, title="Echo Two", artist="Neon Echo", energy=0.78, **common),
        Song(id=3, title="Parade Song", artist="Indigo Parade", energy=0.75, **common),
    ]
    return Recommender(songs)


def _pop_happy_user() -> UserProfile:
    return UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )


def test_without_diversity_top_two_can_repeat_artist():
    # Baseline: the two highest scores are both by the same artist.
    rec = make_artist_cluster_recommender()
    results = rec.recommend(_pop_happy_user(), k=2)
    assert [s.artist for s in results] == ["Neon Echo", "Neon Echo"]


def test_diversity_avoids_repeated_artist():
    # With the penalty on, the second slot goes to the fresh artist instead.
    rec = make_artist_cluster_recommender()
    results = rec.recommend(_pop_happy_user(), k=2, diversity=True)
    artists = [s.artist for s in results]
    assert len(set(artists)) == len(artists)  # no artist appears twice
    assert "Indigo Parade" in artists


def test_diversity_still_returns_k_songs():
    rec = make_artist_cluster_recommender()
    results = rec.recommend(_pop_happy_user(), k=3, diversity=True)
    assert len(results) == 3


def test_recommend_songs_diversity_spreads_artists():
    # Same check on the dict-based path used by the CLI.
    from src.recommender import recommend_songs

    songs = [
        {"title": "Echo One", "artist": "Neon Echo", "genre": "pop", "mood": "happy",
         "energy": 0.80, "acousticness": 0.2},
        {"title": "Echo Two", "artist": "Neon Echo", "genre": "pop", "mood": "happy",
         "energy": 0.78, "acousticness": 0.2},
        {"title": "Parade Song", "artist": "Indigo Parade", "genre": "pop", "mood": "happy",
         "energy": 0.75, "acousticness": 0.2},
    ]
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}

    top2 = recommend_songs(prefs, songs, k=2, diversity=True)
    artists = [song["artist"] for song, _score, _why in top2]
    assert len(set(artists)) == 2
