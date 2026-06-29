# Buzz Score Scoring Logic

## Overview

Each entity tracked in the WatchList receives a **buzzScore** in the range [0, 100] computed daily from Hacker News data. The score is a weighted sum of four components.

---

## The Four Components

| Component | Max Points | Source |
|---|---|---|
| Volume | 30 | Number of HN stories mentioning the entity |
| Engagement | 30 | Total points + total comments across all stories |
| Front Page | 20 | Number of times stories reached the HN front page |
| Acceleration | 20 | Day-over-day change in buzz (cold-start phase: always 0 until a prior snapshot exists) |

**Current observable maximum: 80 points** (acceleration is uniformly zero during cold-start).

---

## Why Log Normalization

Volume and Engagement use log normalization instead of a linear scale:

```
volume_score = 30 × clamp(log(1 + storyCount) / log(1 + VOLUME_REF))
```

HN activity follows a power-law distribution — a viral story can generate 10× the points of a typical one. A linear scale would compress everything into the low end and make the score meaningless for ordinary days. The log scale compresses outliers so that going from 5 → 15 stories feels meaningfully different from going from 150 → 160 stories, which is the right intuition for "buzz."

---

## Calibration Constants

The `*_REF` constants define the input value that earns the full 30/20 points for that component. Inputs above the ref are clamped at the ceiling.

| Constant | Value | Meaning |
|---|---|---|
| `VOLUME_REF` | 30 | 30 stories/day → full volume score |
| `ENGAGEMENT_REF` | 1000 | 1000 combined points+comments → full engagement score |
| `FRONTPAGE_REF` | 5 | 5 front-page appearances → full front-page score |

### Why Fixed Constants, Not Cross-Entity Maxima

An earlier spec draft defined normalization using the busiest entity in the current run as the denominator — a relative leaderboard where every entity is scored against today's field. That approach was deliberately rejected.

Mycroft's coordination layer consumes buzz scores as a time-series signal: it computes velocity, trailing averages, and acceleration across days. A relative scale breaks this — a quiet week inflates every score and a busy week compresses them, making cross-day comparisons meaningless. An entity that scores 60 on a quiet Tuesday and 40 on a busy Friday would appear to be declining when the underlying activity was identical.

Fixed constants produce an absolute scale: the same activity always produces the same score regardless of what other entities did that day. This is what time-series comparability requires. **Do not change normalization to cross-entity maxima** — it would break velocity and acceleration computation in the live phase.

### How the Fixtures Justified These Values

Four fixture cases were used to validate that the bands are well-separated and intuitive:

| Fixture | storyCount | engagement | frontPage | lowConf | Score | Band |
|---|---|---|---|---|---|---|
| Busy | 30 | 4500 | 6 | false | 80.0 | 75–90 |
| Moderate | 10 | 600 | 1 | false | 52.7 | 40–60 |
| Sparse | 2 | 30 | 0 | true | 38.0 | < 45 |
| Zero-hit | 0 | 0 | 0 | true | 0.0 | exactly 0 |

The constants were chosen so that:
- A "busy" entity saturates volume and engagement (both hit the log ceiling) and scores ~80.
- A "moderate" entity sits clearly in the middle band without clustering near busy or zero.
- At least a 14-point gap separates each band, making the leaderboard ranking meaningful.

---

## Sparse-Entity Floor (Low-Confidence Path)

When an entity has **fewer than 3 stories** in the lookback window, the log scale becomes unreliable — a single story is too noisy to normalize against a 30-story reference. These entities are flagged `lowConfidence: true` upstream and scored on an **absolute linear scale** instead:

```
volume_score     = 30 × clamp(storyCount / 3)
engagement_score = 30 × clamp(engagement / 50)
front_page_score = 0   # suppressed entirely; one front-page hit on 1 story is noise
```

This floor path ensures sparse entities:
- Can still score nonzero (a single story with 20 points isn't worthless).
- Never outscore moderate entities due to a lucky viral hit on thin volume.
- Are visually identifiable in the output via `lowConfidence: true`.

---

## Cold-Start Acceleration

The acceleration component measures **day-over-day velocity** — how much the buzz score changed compared to the previous snapshot. This requires a historical baseline stored in the database.

During the **cold-start phase** (no prior snapshot exists in the database for the entity), acceleration is hardcoded to zero for all entities uniformly:

```python
accel_score = 0.0
```

The uniformity is deliberate: every entity reads zero, so early scores are comparably conservative rather than variably distorted. All entities carry `coldStart: true` in their output while in this state.

---

## What Changes in the Live Phase

Once the scoring node is wired to Supabase, the live phase begins:

1. **After scoring**, today's `buzzScore` is written to a `buzz_snapshots` table keyed by `(entity, runDate)`.
2. **Before scoring**, yesterday's snapshot is read back.
3. Acceleration is computed as:

   ```python
   if yesterday_buzz == 0:
       # Entity had no prior activity. Emergence from zero is already captured
       # by Volume and Engagement; no additional acceleration credit is awarded.
       accel_score = 0.0
   else:
       delta = today_buzz - yesterday_buzz
       accel_score = 20 × clamp(delta / yesterday_buzz, 0, 1)
   ```

   **Asymmetry is deliberate.** `clamp(x, 0, 1)` floors acceleration at zero. An entity
   that declined gets `accel_score = 0`, not a negative value. This is a design choice,
   not an oversight: declining attention is already captured by falling Volume and Engagement
   scores. The acceleration component rewards breakout momentum only — it does not
   double-penalize decline. The consequence is that `buzzScore` can range [0, 100] on an
   upswing and [0, 80] during sustained decline (acceleration contributes nothing either way
   in the downward direction). The coordination layer should be aware of this ceiling
   asymmetry when interpreting scores.

4. `coldStart` flips to `false` once a prior snapshot exists for the entity.
5. The observable maximum rises from 80 to 100.
