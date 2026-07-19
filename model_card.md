# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

The name says what it does. You tell it your vibe, and it finds songs that match.

---

## 2. Goal / Task  

VibeMatch suggests songs from a small catalog that fit a listener's taste.

- You give it a taste profile: a favorite genre, a mood, an energy level, and whether you like acoustic music.
- It looks at every song and picks the five that fit your profile best.
- It also tells you *why* it picked each song, in plain words.

It does not predict the future or learn from other people. It just matches songs to what you asked for.

---

## 3. How the Model Works  

Think of it like a scorecard. Every song starts at zero points. Then the song earns points for matching your taste:

- **Genre:** if the song's genre is exactly your favorite genre, it earns 2 points.
- **Mood:** if the song's mood is exactly your favorite mood, it earns 1.5 points.
- **Energy:** the closer the song's energy is to the energy level you asked for, the more points it earns, up to 2 points. A perfect match gets the full 2. The further off, the fewer points.
- **Acoustic:** if the song being acoustic (or not) matches what you said you like, it earns 0.5 points.

The song adds up its points. Then VibeMatch sorts every song from highest score to lowest and shows you the top five. The points are set up so genre and a perfect energy match matter most, mood matters a little less, and the acoustic preference is just a small tiebreaker.

There is also an optional **diversity penalty**. When it is on, VibeMatch does not just take the five top scores — it builds the list one song at a time and quietly lowers a song's score if the same artist or genre is already in the list (an artist repeat costs more than a genre repeat). That way you do not get five songs from the same artist, and a fresh song can bump a repeat. It is off by default and can be turned on per request.

I did not change the core scoring rules from the starter idea, but I tested them hard to see where they break (see Evaluation).

---

## 4. Data  

The catalog is a single CSV file with **18 songs**.

Each song has: a title, an artist, a genre, a mood, an energy level (0 to 1), a tempo, a valence (how positive it sounds), a danceability, and an acousticness.

- **Genres:** 15 different ones. Most show up only once. Only lofi (3 songs) and pop (2 songs) repeat.
- **Moods:** 14 different ones, and most are used only once.
- I did not add or remove any songs. I used the catalog as given.

Some parts of musical taste are missing. There is no rap-vs-sung info, no language or lyrics, and no year or popularity. The catalog is also very small, so many genres have just one song to offer. There is even a gap in the energy values: nothing sits between 0.55 and 0.75.

---

## 5. Strengths  

VibeMatch works well when a user gives a clear, normal profile that matches the catalog's words.

- **Clear-taste users get good results.** A pop-and-happy fan gets pop and happy songs at the top. A lofi-and-chill fan gets calm lofi tracks. The picks match what you would expect.
- **Each preference actually does something.** In my tests, turning energy up pulled in loud songs and turning it down pulled in calm ones. Changing the mood word swapped which song came first. So the dials really work.
- **Variety across users.** Eight different profiles gave eight different top songs. No single song hogs the top spot.
- **It explains itself.** Every recommendation lists the reasons and the points add up to the score, so you can see exactly why a song was picked.

---

## 6. Observed Behavior / Biases 

Here are the patterns and unfair spots I noticed while testing.

- **It only knows exact words.** "pop" and "indie pop" count as total strangers. A typo like "Pop" matches nothing. If your word is not in the catalog, that part of your taste is just ignored.
- **Rare genres get thin lists.** Most genres have only one song. So a metal fan or a reggae fan can only ever get their one genre song. The rest of their list is filled by energy, not by genre.
- **Lofi fans get a bubble.** Lofi has three songs, so lofi lovers get a nice full list of lofi. Everyone else gets less. That is unfair based on which genre you happen to like.
- **It ignores some features.** The songs have tempo, valence, and danceability, but the scoring never uses them. So a user who cares about "something danceable" has no way to ask for it.
- **No guardrails.** Weird input does not get caught (see Evaluation). Bad profiles still return a confident-looking list.

The main bias I want to call out is below.

**Weakness: the energy score quietly underserves moderate-energy listeners.**
Because the energy fit is a symmetric linear formula (`1.0 - |song_energy - target|`)
and energy is the only feature scored for *every* song, the amount of ranking
influence a user's energy preference carries depends on where that preference
sits. When I swept different targets, an extreme request (target ≈ 1.0) spread the
energy points across a wide 1.4-point range, while a moderate request (target ≈
0.65) compressed them into just 0.54 points — so a moderate listener's stated
preference barely moves the ranking and the result is decided instead by genre and
the acoustic tiebreaker. This is made worse by a gap in the dataset itself: no song
falls between 0.55 and 0.75 energy, so a perfectly ordinary "pleasantly upbeat"
user can never be matched within 0.10 of any track and always gets recommendations
that are either too mellow or too intense. In short, the system listens most
closely to users with extreme energy tastes and effectively ignores those in the
middle.

---

## 7. Evaluation Process  

I checked the recommender by running many profiles through it and reading the top
results by hand. I did three kinds of tests: normal profiles, an energy sweep, and
adversarial "try to break it" profiles. Here is what I ran and what I found.

### User profiles I tested

I evaluated the recommender in three passes. First, **realistic profiles** — one
per genre family, each pairing a genre with its natural mood and a fitting energy
(e.g. `pop / happy / 0.8`, `rock / intense / 0.9`, `lofi / chill / 0.4`,
`classical / melancholy / 0.3`, `edm / euphoric / 0.95`) — to confirm the system
gives sensible, on-taste results for ordinary users. Second, an **energy sweep**,
holding genre fixed while moving `target_energy` from 0.0 to 1.0, to see how much
the energy term actually shifts the ranking at different targets. Third, a set of
**adversarial / edge-case profiles** designed to break the scoring logic:
internally conflicting tastes (`mood=sad` with `energy=0.9`), out-of-range energy
(5.0 and −1.0), typos and wrong casing (`Pop`, `Happy`), unknown labels
(`genre=k-pop`), an empty profile `{}`, and type-confused inputs
(`likes_acoustic="yes"`). For each profile I looked at whether the top 5 were
actually relevant, whether the printed reasons summed to the score, and whether the
system failed loudly or silently.

### What surprised me

The realistic pass was reassuring — eight different profiles produced eight
different #1 songs, so no single track dominates and genre is *not* over-weighted
the way I feared. The surprises came from the edge cases. (1) The scorer never
validates input, so `energy=5.0` produced **negative scores** that were still
presented as "top recommendations." (2) Wrong casing or an unknown genre silently
scores every song 0.00 and the list falls back to raw catalog order, so a broken
profile *looks* like a working one — the system fails silently instead of warning.
(3) Most striking, a user who typed `genre=k-pop` (matching nothing) but
`mood=melancholy` (which does exist) got a **classical** song as their #1 pick —
genre was ignored entirely and mood alone drove a result the user would never
expect. Together these showed me that the code "works" on well-formed input but has
no guardrails for the messy, inconsistent input real users actually produce.

### Profile comparisons

To check that each preference actually changes the output in a way that makes
sense, I ran contrasting pairs of profiles and compared their top results.

**Pair A — high energy vs. low energy.** The EDM / euphoric / 0.95 profile puts
loud, electronic tracks on top (Neon Horizon, then high-energy songs like Gym Hero
and Iron Verdict), while the lofi / chill / 0.40 profile fills the top with quiet,
mellow tracks (Midnight Coding, Library Rain, Focus Flow). *This makes sense: the
energy target is doing exactly its job — turning it up pulls in intense songs, and
turning it down pulls in calm ones. It confirms that energy is a real, working
dial and not just decoration.*

**Pair B — likes acoustic vs. dislikes acoustic** (energy held the same at 0.40, so
only the acoustic preference differs). The acoustic-lover gets guitar-and-piano,
high-acousticness songs on top (Focus Flow, Midnight Coding, Coffee Shop Stories,
all with acousticness above 0.7), while the acoustic-averse profile shifts toward
more electronic, low-acousticness tracks (Slow Confession and Island Time, both
around 0.3–0.4). *This makes sense: with energy fixed, the only thing separating
the two lists is the acoustic point, so the same "calm" request tips toward
unplugged songs for one user and produced/electronic songs for the other. It also
shows the acoustic term is weak — it only reshuffles the list by half a point and
never overturns a strong genre or energy match.*

**Pair C — same genre, different mood** (pop / happy vs. pop / intense, energy the
same). The happy profile ranks Sunrise City (a happy pop song) first, while the
intense profile flips Gym Hero (an intense pop song) into first and drops Sunrise
City to second. *This makes sense: both songs are pop with strong energy, so genre
and energy roughly tie them — the mood word is the tiebreaker that decides which
one wins. It's good evidence that mood is pulling its weight, quietly picking the
emotionally right song out of two otherwise-similar candidates.*

### Adversarial / edge-case evaluation

Beyond ordinary profiles, I ran a set of adversarial profiles (via
`python -m src.adversarial`) built to trick the scoring logic. The raw terminal
output for each is below.

**1. Conflicting energy vs. mood** — `sad` matched no song, so mood dropped out
silently and recs were driven by genre + energy only:

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

**2. Energy above range (5.0)** — no clamping, so every score goes negative:

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

**3. Energy below range (-1.0)** — same missing clamp, scores dip below zero:

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

**4. Typo / wrong casing** — exact, case-sensitive matching → five songs tie at 0.00:

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

**5. Unknown genre + valid mood** — `k-pop` matched nothing but `melancholy` did,
so a k-pop fan's top pick is a classical track:

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

**6. Empty profile** — every song scores 0.00; ranking falls back to CSV order:

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

**7. Acoustic freebie (`likes_acoustic=False`)** — the +0.5 is awarded to nearly
every song, so it barely discriminates:

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

**8. Weight collision (`genre` and perfect `energy` both worth 2.0)** — a rock
song with far-off energy barely beats low-energy non-rock songs:

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

**9. Type confusion (`likes_acoustic="yes"`)** — truthy string `== bool` is always
`False`, so the term silently vanishes:

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

## 8. Intended Use and Non-Intended Use  

**What it is for:**

- A classroom project to learn how a simple recommender turns data into picks.
- Exploring how different taste profiles change the results.
- A tiny demo of content-based matching that anyone can read and understand.

**What it should not be used for:**

- Real users or a real music app. The catalog is only 18 songs.
- Any decision that matters. It has no input checking and can return bad lists.
- Judging real artists or genres. The tags are hand-made and the data is too small to be fair.

---

## 9. Ideas for Improvement  

If I kept building this, I would:

1. **Add input checks.** Keep energy between 0 and 1, ignore case, and warn the user when a genre or mood matches nothing. This fixes the silent failures I found in testing.
2. **Use the features I already have.** Score valence, tempo, and danceability too, so users can ask for "positive," "fast," or "danceable" songs.
3. **Allow near matches.** Treat "pop" and "indie pop" as close instead of strangers, so fans of rare genres still get relevant picks. (I already added a **diversity penalty** that keeps the top five from stacking up on one artist or genre — the next step is the near-match part.)

---

## 10. Personal Reflection  

I learned that a recommender is really just a scorecard plus a sort. Once I saw the
points add up, the "magic" felt a lot simpler. The surprising part was how easy it
was to break. A single typo, or an energy number out of range, gave confident but
wrong results, and the system never said anything was off. That changed how I think
about real music apps. Now I picture the hidden scoring behind every suggestion,
and I wonder what quiet biases are baked in that I never see.
