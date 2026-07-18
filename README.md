# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

Big platforms like Spotify and TikTok predict what you'll love next by combining two strategies: collaborative filtering, which learns from the behavior of millions of other users ("people who liked what you liked also liked this"), and content-based filtering, which looks at the actual attributes of the songs themselves. They blend these into hybrid systems and run them through a pipeline — score a huge pool of candidate songs, rank the best ones, then apply rules for variety and freshness. My simulation implements the content-based half of that idea, at small scale. It needs no other users' data: it describes each song by its features, stores the listener's taste as a profile, and scores every song by how well it matches that profile. My version prioritizes closeness of fit over popularity — a song wins not by being loud or fast, but by sitting near the user's stated preferences for genre, mood, and energy level. The tradeoff I'm accepting is that this makes my recommender immune to the "cold start" problem (it works for a brand-new user instantly) but vulnerable to the "filter bubble" (it tends to suggest more of what the user already likes rather than surprising them).

Features my Song object uses:

> genre — style category (pop, lofi, rock, jazz, ambient, …)
> mood — emotional feel (happy, chill, intense, focused, …)
> energy — intensity level, 0.0–1.0
> tempo_bpm — speed in beats per minute
> valence — musical positivity, 0.0–1.0
> danceability — how danceable the track is, 0.0–1.0
> acousticness — how acoustic vs. electronic, 0.0–1.0
(id, title, and artist are stored for identification but are not used as scoring features.)

Information my UserProfile stores:

> favorite_genre — the genre the listener prefers
> favorite_mood — the mood the listener is after
> target_energy — the energy level they want, 0.0–1.0
> likes_acoustic — whether they lean toward acoustic music (True/False)

How the score is computed and songs are chosen: the Recommender scores each song individually — awarding points for matching the user's genre and mood, and rewarding songs whose energy is close to target_energy (proximity, not just high energy). It then ranks all songs by score and returns the top k.

### Algorithm Recipe

For every song in the catalog, I start the score at `0.0` and add points as follows:

1. **Genre match (+2.0):** if the song's `genre` exactly equals the user's `favorite_genre`, add 2.0. Otherwise add nothing.
2. **Mood match (+1.5):** if the song's `mood` exactly equals the user's `favorite_mood`, add 1.5. Otherwise add nothing.
3. **Energy fit (+0.0 to +2.0, scaled):** measure closeness as `1.0 - abs(song.energy - target_energy)`, then add `2.0 × closeness`. A perfect match adds the full 2.0; the score falls off linearly the further the song's energy is from the target.
4. **Acoustic preference (+0.5):** treat a song as "acoustic" if `acousticness > 0.5`. If that True/False label matches the user's `likes_acoustic`, add 0.5.

Then **rank all songs by total score, highest first, and return the top `k`** (default 5). Ties keep their original catalog order.

The relative weights encode my priorities: **genre and a perfect energy fit are worth the most (2.0 each), mood is close behind (1.5), and acoustic feel is a light tiebreaker (0.5).** Only genre and energy can single-handedly separate two songs; mood and acoustic mostly break ties. These weights live at the top of `recommender.py` so they are easy to tune (see *Experiments You Tried*).

### Potential Biases I Expect

- **Genre over-prioritization.** Because an exact genre match is worth the most and pays out all-or-nothing, the system may over-prioritize genre and overlook great songs that match the user's mood and energy but carry a different genre label. A "happy, high-energy" listener whose favorite genre is `pop` will be steered toward pop tracks even when an `indie pop` or `edm` song is a better emotional fit.
- **Rigid label matching.** Genre and mood must match *exactly* — `pop` and `indie pop` score as complete strangers, and `chill` earns nothing against `relaxed` or `laid-back` even though they're near-synonyms. The model has no notion of similar-but-not-identical labels.
- **Filter bubble.** Since songs win by sitting close to what the user already stated, the recommender reinforces existing taste and rarely surprises the listener with something new — the same tradeoff real platforms fight with "discovery" features.
- **Tiny, hand-authored catalog.** With only 18 songs and human-assigned genre/mood tags, any labeling quirk in the data set is amplified, and sparse genres (one metal song, one reggae song) can never form a strong recommendation on their own.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Running `python -m src.main` against the 18-song catalog with the profile
`genre=pop, mood=happy, energy=0.8` produces:

```
Loaded songs: 18

========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=pop, mood=happy, energy=0.8
========================================================

  1. Sunrise City  —  Neon Echo
     score: 5.46
     why:
       • genre match: pop (+2.0)
       • mood match: happy (+1.5)
       • energy 0.82 vs target 0.8 (+1.96)

  2. Gym Hero  —  Max Pulse
     score: 3.74
     why:
       • genre match: pop (+2.0)
       • energy 0.93 vs target 0.8 (+1.74)

  3. Rooftop Lights  —  Indigo Parade
     score: 3.42
     why:
       • mood match: happy (+1.5)
       • energy 0.76 vs target 0.8 (+1.92)

  4. Block Party  —  Cassette King
     score: 1.90
     why:
       • energy 0.85 vs target 0.8 (+1.90)

  5. Night Drive Loop  —  Neon Echo
     score: 1.90
     why:
       • energy 0.75 vs target 0.8 (+1.90)
```

Notice how the reasons sum to the score (e.g. 2.0 + 1.5 + 1.96 = 5.46), so
every recommendation is fully explainable.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



