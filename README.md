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

### Diversity Penalty (optional)

By default the top `k` is just the highest-scoring songs, which can stack the list
with the same artist or genre. Turning on the **diversity penalty** spreads the
results out. Instead of sorting once, it builds the list one song at a time and
penalizes any candidate that repeats something already chosen:

- **−1.5** for every song already in the list by the **same artist**
- **−0.75** for every song already in the list in the **same genre**

The first song from an artist or genre is never penalized; the penalty only grows
as repeats pile up. This lets a slightly lower-scoring but *fresh* song beat a second
song from an artist who is already represented. For a `lofi / chill / 0.4` profile,
this drops the second song by the same lofi artist out of the top 5 and pulls in an
ambient, a jazz, and a folk track instead.

Enable it with `recommend_songs(..., diversity=True)` (or `Recommender.recommend(..., diversity=True)`),
or from the command line:

```bash
python -m src.main balanced diverse
```

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

### Adversarial / Edge-Case Profiles

To stress-test the scoring logic I built a harness ([`src/adversarial.py`](src/adversarial.py),
run with `python -m src.adversarial`) that feeds it profiles designed to expose
weaknesses. The raw terminal output for each is below.

**1. Conflicting energy vs. mood** — mood and energy are scored independently,
so a "sad" + high-energy profile can't be satisfied by one song. The catalog has
no `sad` song at all, so the mood constraint silently evaporates and the recs are
driven purely by genre + energy:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=pop, mood=sad, energy=0.9
========================================================

  1. Gym Hero  —  Max Pulse
     score: 3.94
     why:
       • genre match: pop (+2.0)
       • energy 0.93 vs target 0.9 (+1.94)

  2. Sunrise City  —  Neon Echo
     score: 3.84
     why:
       • genre match: pop (+2.0)
       • energy 0.82 vs target 0.9 (+1.84)

  3. Storm Runner  —  Voltline
     score: 1.98
     why:
       • energy 0.91 vs target 0.9 (+1.98)

  4. Neon Horizon  —  Pulse Theory
     score: 1.90
     why:
       • energy 0.95 vs target 0.9 (+1.90)

  5. Block Party  —  Cassette King
     score: 1.90
     why:
       • energy 0.85 vs target 0.9 (+1.90)
```

**2. Energy above range (5.0) — no clamping.** `proximity_score` is never
bounded, so every score goes negative and the "top" recommendation has a score
of −4.18:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=rock, energy=5.0
========================================================

  1. Storm Runner  —  Voltline
     score: -4.18
     why:
       • genre match: rock (+2.0)
       • energy 0.91 vs target 5.0 (+-6.18)

  2. Iron Verdict  —  Ashfall
     score: -6.04
     why:
       • energy 0.98 vs target 5.0 (+-6.04)

  3. Neon Horizon  —  Pulse Theory
     score: -6.10
     why:
       • energy 0.95 vs target 5.0 (+-6.10)

  4. Gym Hero  —  Max Pulse
     score: -6.14
     why:
       • energy 0.93 vs target 5.0 (+-6.14)

  5. Block Party  —  Cassette King
     score: -6.30
     why:
       • energy 0.85 vs target 5.0 (+-6.30)
```

**3. Energy below range (-1.0) — no clamping.** Negative target distorts the
energy axis; scores again dip below zero:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=rock, energy=-1.0
========================================================

  1. Storm Runner  —  Voltline
     score: 0.18
     why:
       • genre match: rock (+2.0)
       • energy 0.91 vs target -1.0 (+-1.82)

  2. Spacewalk Thoughts  —  Orbit Bloom
     score: -0.56
     why:
       • energy 0.28 vs target -1.0 (+-0.56)

  3. Winter Elegy  —  Aria Solenne
     score: -0.60
     why:
       • energy 0.3 vs target -1.0 (+-0.60)

  4. Library Rain  —  Paper Lanterns
     score: -0.70
     why:
       • energy 0.35 vs target -1.0 (+-0.70)

  5. Coffee Shop Stories  —  Slow Stereo
     score: -0.74
     why:
       • energy 0.37 vs target -1.0 (+-0.74)
```

**4. Typo / wrong casing — silent zero.** Matching is exact and case-sensitive,
so `Pop`/`Happy` match nothing and five songs tie at 0.00:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=Pop, mood=Happy
========================================================

  1. Sunrise City  —  Neon Echo
     score: 0.00
     why:
       • a broad match for your taste

  2. Midnight Coding  —  LoRoom
     score: 0.00
     why:
       • a broad match for your taste

  3. Storm Runner  —  Voltline
     score: 0.00
     why:
       • a broad match for your taste

  4. Library Rain  —  Paper Lanterns
     score: 0.00
     why:
       • a broad match for your taste

  5. Gym Hero  —  Max Pulse
     score: 0.00
     why:
       • a broad match for your taste
```

**5. Unknown genre + valid mood.** `k-pop` matches nothing, but `melancholy`
*does* exist — so a self-described k-pop fan's #1 recommendation is a **classical**
track. Genre was ignored; mood alone drove the result:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=k-pop, mood=melancholy
========================================================

  1. Winter Elegy  —  Aria Solenne
     score: 1.50
     why:
       • mood match: melancholy (+1.5)

  2. Sunrise City  —  Neon Echo
     score: 0.00
     why:
       • a broad match for your taste

  3. Midnight Coding  —  LoRoom
     score: 0.00
     why:
       • a broad match for your taste

  4. Storm Runner  —  Voltline
     score: 0.00
     why:
       • a broad match for your taste

  5. Library Rain  —  Paper Lanterns
     score: 0.00
     why:
       • a broad match for your taste
```

**6. Empty profile.** No signal at all: every song scores 0.00 and the ranking
silently falls back to raw CSV order:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: 
========================================================

  1. Sunrise City  —  Neon Echo
     score: 0.00
     why:
       • a broad match for your taste

  2. Midnight Coding  —  LoRoom
     score: 0.00
     why:
       • a broad match for your taste

  3. Storm Runner  —  Voltline
     score: 0.00
     why:
       • a broad match for your taste

  4. Library Rain  —  Paper Lanterns
     score: 0.00
     why:
       • a broad match for your taste

  5. Gym Hero  —  Max Pulse
     score: 0.00
     why:
       • a broad match for your taste
```

**7. Acoustic freebie (`likes_acoustic=False`).** A non-acoustic song *also*
earns the +0.5 match, so nearly every song collects the point — it barely
discriminates and produces a wall of ties:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: likes_acoustic=False
========================================================

  1. Sunrise City  —  Neon Echo
     score: 0.50
     why:
       • acoustic preference match (+0.5)

  2. Storm Runner  —  Voltline
     score: 0.50
     why:
       • acoustic preference match (+0.5)

  3. Gym Hero  —  Max Pulse
     score: 0.50
     why:
       • acoustic preference match (+0.5)

  4. Night Drive Loop  —  Neon Echo
     score: 0.50
     why:
       • acoustic preference match (+0.5)

  5. Rooftop Lights  —  Indigo Parade
     score: 0.50
     why:
       • acoustic preference match (+0.5)
```

**8. Weight collision (`genre` and a perfect `energy` fit are both worth 2.0).**
A rock song with far-from-target energy barely edges out low-energy non-rock
songs, making the intended priority ambiguous:

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: genre=rock, energy=0.0
========================================================

  1. Storm Runner  —  Voltline
     score: 2.18
     why:
       • genre match: rock (+2.0)
       • energy 0.91 vs target 0.0 (+0.18)

  2. Spacewalk Thoughts  —  Orbit Bloom
     score: 1.44
     why:
       • energy 0.28 vs target 0.0 (+1.44)

  3. Winter Elegy  —  Aria Solenne
     score: 1.40
     why:
       • energy 0.3 vs target 0.0 (+1.40)

  4. Library Rain  —  Paper Lanterns
     score: 1.30
     why:
       • energy 0.35 vs target 0.0 (+1.30)

  5. Coffee Shop Stories  —  Slow Stereo
     score: 1.26
     why:
       • energy 0.37 vs target 0.0 (+1.26)
```

**9. Type confusion (`likes_acoustic="yes"`).** The truthy string is compared
with `==` against a bool, which is always `False`, so the term silently vanishes
— "looks configured, does nothing":

```
========================================================
  🎵  Top 5 recommendations
      for taste profile: likes_acoustic=yes
========================================================

  1. Sunrise City  —  Neon Echo
     score: 0.00
     why:
       • a broad match for your taste

  2. Midnight Coding  —  LoRoom
     score: 0.00
     why:
       • a broad match for your taste

  3. Storm Runner  —  Voltline
     score: 0.00
     why:
       • a broad match for your taste

  4. Library Rain  —  Paper Lanterns
     score: 0.00
     why:
       • a broad match for your taste

  5. Gym Hero  —  Max Pulse
     score: 0.00
     why:
       • a broad match for your taste
```

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

### Personal Reflection on My Engineering Process

My biggest learning moment was not writing the scoring rules — it was trying to
break them. The recommender looked finished and correct when I fed it normal
profiles. But when I built a set of adversarial profiles (conflicting tastes,
out-of-range energy, typos, empty input), it fell apart in quiet ways. An energy
value of 5.0 produced negative scores that were still shown as "top picks." A typo
in the genre made every song tie at zero, and the list just fell back to catalog
order while still looking like a real recommendation. That was the moment the
project clicked for me: the hard part of engineering is not making something work
on the happy path, it is figuring out how it fails on the messy input real users
actually type.

Using AI tools sped up the parts that would have taken me a long time by hand. They
helped me build the test harness, run many profiles at once, and turn raw output
into clear tables and comparisons. Where I had to double-check was the *reasoning*,
not the typing. When a tool claimed one song was "dominating" the results, I ran an
actual sweep of eight profiles and saw eight different winners — so the claim was
wrong, and the real issue was elsewhere. I also had to verify the math myself: I
checked that the reason lines still added up to the score after I changed the code,
and I caught that two "tied" songs were actually separated by a tiny floating-point
difference. The tools were great at doing and explaining, but I still had to be the
one who confirmed the numbers were true.

What surprised me most was how much a plain scorecard can *feel* like a real
recommendation. There is no learning, no neural network, no data from other
users — just add up a few points and sort. Yet when the top result is a happy pop
song for a happy pop fan, complete with reasons, it feels smart. That made me
realize how much of the "intelligence" we sense in apps like Spotify might be
simpler scoring than we assume, and how easily a simple rule can hide a bias in
plain sight (like my energy formula quietly ignoring moderate-energy listeners).

If I extended this project, I would first add real input validation so bad
profiles fail loudly instead of silently. Next I would use the features the dataset
already has but the model ignores — valence, tempo, and danceability — so users
could ask for more than genre, mood, and energy. Finally I would add near-match
scoring and a diversity rule, so "pop" and "indie pop" are treated as cousins and
the top five are not all the same genre. That would make the recommendations feel
less like a strict filter and a little more like discovery.



