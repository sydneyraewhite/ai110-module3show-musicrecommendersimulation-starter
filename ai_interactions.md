# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude (Claude Code) as an agent to help me stress-test and then extend my
music recommender. The work happened in several steps: probe the scoring logic with
adversarial user profiles, run those profiles to observe the output, document the
findings in my README and model card, and finally expand the dataset with new
attributes and update the scoring logic to use them.

**Prompts used:**

Some of the key prompts I gave, in order:

- *"Suggest 'adversarial' or 'edge case' user profiles — profiles designed to see
  if my scoring logic can be tricked or produces unexpected results (e.g., a user
  with conflicting preferences like energy: 0.9 and mood: sad)."*
- *"Run the recommender for each profile so we can observe the top 5 results in the
  terminal."*
- *"Temporarily comment out the mood check to see how the rankings change... then
  verify the math remains valid and note whether it made the recommendations more
  accurate or just different."*
- *"Identify potential 'filter bubbles' or biases in my current scoring logic —
  does my system ignore certain types of users because of how I calculate the
  energy gap?"*
- *"Introduce 5 or more complex attributes to my dataset that are not currently
  present (e.g., Song Popularity 0-100, Release Decade, Detailed Mood Tags), and
  update both data/songs.csv and the scoring logic in src/recommender.py so scoring
  accounts for the new attributes."*

**What did the agent generate or change?**

- Created `src/adversarial.py`, a harness that runs nine edge-case profiles
  (conflicting taste, out-of-range energy, typos, unknown labels, empty profile,
  type-confused input) and prints the top 5 for each.
- Ran the harness and a sweep of realistic profiles, then wrote the results into
  `README.md` (Experiments section) and `model_card.md` (Evaluation section) as
  fenced code blocks plus plain-language comparisons.
- Analyzed the data distribution and documented an energy-gap bias (moderate-energy
  users are underserved) in the model card's Limitations section.
- Completed every section of `model_card.md` (name, goal, algorithm, data,
  strengths, biases, evaluation, intended use, improvements, reflection).
- Added six new columns to `data/songs.csv` for all 18 songs: `popularity`,
  `release_decade`, `mood_tags`, `language`, `instrumentalness`, and `explicit`.
- Updated `src/recommender.py`: new scoring weights, extra fields on the `Song` and
  `UserProfile` dataclasses (with defaults), CSV parsing for the new columns, and
  matching scoring rules in both the OOP `_score` method and the dict-based
  `score_song` function.

**What did you verify or fix manually?**

- **I checked the agent's claims instead of trusting them.** When it suggested the
  Genre weight might be "too strong" because one song kept appearing, I had it run
  an 8-profile sweep — that gave 8 different winners, disproving the claim. The real
  repeat was only in the zero-score tie cases (CSV fallback order).
- **I verified the math by hand.** After the mood check was commented out, I
  confirmed every reason line still summed to the printed score, and I noticed two
  songs that looked "tied" at 1.90 were actually separated by a tiny floating-point
  difference.
- **I made the agent revert a temporary change.** The mood-check comment-out was for
  an experiment only; I had it restored and confirmed with `git diff` that the file
  matched the original commit.
- **I ran the tests and the new attributes myself.** `pytest` still passes (the new
  dataclass fields have defaults, so the existing tests were not broken), the new
  columns parse to the right types, and both scoring paths (OOP and dict) produce
  the same score of 9.57 on a detailed profile.
- **I flagged, rather than accepted, silent doc drift.** Adding new attributes made
  some README and model-card sections out of date, and the agent pointed this out
  and left them for me to decide instead of quietly rewriting everything.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**. I wanted the user to switch between different ranking
"modes" — Genre-First, Mood-First, and Energy-Focused — without rewriting the
scoring logic each time. The Strategy pattern lets me define each mode as its own
interchangeable object and swap it in at runtime.

**How did AI help you brainstorm or implement it?**

I asked the AI to help me build multiple ranking strategies and to brainstorm a
design pattern that would keep the code modular. The useful part of the
conversation was that it did *not* jump straight to the most "textbook" version.

- My first instinct was that each strategy should be its own class with its own
  `score()` method. The AI pointed out that all three modes actually run the *same*
  scoring algorithm and only differ in how much each feature is weighted. Giving
  each strategy its own full scoring method would duplicate the whole scoring loop,
  which is not DRY and would be a pain to keep in sync when I add features.
- So the AI suggested a lighter version of the Strategy pattern: make a strategy a
  small object that just holds a *named bundle of weights*, and have the scoring
  functions read the weights from whichever strategy is passed in. Same algorithm,
  interchangeable weight profiles.
- It also flagged a nice safety property: if the default strategy ("Balanced")
  uses the original weight values, then all my old code and tests behave exactly
  as before, so adding the pattern was a non-breaking change. I confirmed this by
  running `pytest` — both tests still pass.

I decided this trade-off was the right call for my project: it is clearly still the
Strategy pattern (interchangeable, injected behavior objects), but it avoids
copy-pasting the scoring logic four times.

**How does the pattern appear in your final code?**

In `src/recommender.py`:

- `RankingStrategy` is a frozen dataclass that holds one set of scoring weights and
  a `name`.
- `BALANCED`, `GENRE_FIRST`, `MOOD_FIRST`, and `ENERGY_FOCUSED` are the concrete
  strategy objects, and `STRATEGIES` is a dict that maps a lowercase key to each.
- The scoring functions (`Recommender._score` and the functional `score_song` /
  `recommend_songs`) take a `strategy` argument and read `strategy.w_genre`,
  `strategy.w_mood`, etc. instead of hard-coded constants. The default is
  `BALANCED`.

In `src/main.py`:

- The user picks a mode on the command line, e.g. `python -m src.main energy-focused`,
  or runs with no argument to see the same profile ranked under every mode. Switching
  modes is a one-object swap — no scoring code changes.
